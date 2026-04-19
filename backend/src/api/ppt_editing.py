from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, UploadFile, File, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import asyncio
import json
import time
import logging
import copy
from datetime import datetime
import os
import re

from ..core.database import get_db, SessionLocal
from ..models.ppt_document import PPTDocument
from ..models.document import MAX_VERSION_HISTORY
from ..models.user import User
from ..core.security import get_current_user, get_optional_user, get_optional_user_for_sse
from ..services.editor_processor import get_editor_processor
from sqlalchemy.orm.attributes import flag_modified

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

web_router = APIRouter()
ppt_router = APIRouter()

# In-process SSE event registry: (document_id, slide_number) -> asyncio.Event
_ppt_edit_events: Dict[tuple, asyncio.Event] = {}


class CitationItem(BaseModel):
	id: int
	index: int
	html: str
	selector: str
	note: Optional[str] = None


class PPTEditRequest(BaseModel):
	document_id: int
	slide_number: int
	citations: List[CitationItem]
	user_prompt: str
	thinking_enabled: Optional[bool] = None
	model: Optional[str] = None  # 'claude-sonnet-4-6', 'claude-opus-4-6', 'claude-haiku-4-5-20251001', 'glm-4.7', 'glm-4.6'


class WebEditResponse(BaseModel):
	status: str
	message: str
	modified_html: Optional[str] = None
	error: Optional[str] = None


class KeepVersionRequest(BaseModel):
	version: str  # 'before' | 'after'


class InteractiveOrderItem(BaseModel):
	type: str  # 'slide' | 'demo'
	slide_number: int


class InteractiveOrderRequest(BaseModel):
	order: List[InteractiveOrderItem]


# ============================================================================
# Helper functions for access control and common operations
# ============================================================================

def _get_ppt_document_or_404(document_id: int, db: Session) -> PPTDocument:
	document = db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
	if not document:
		raise HTTPException(status_code=404, detail="Document not found")
	return document


def _ensure_ppt_access(document: PPTDocument, current_user: Optional[User]) -> None:
	"""Allow access if document is public OR user owns the document."""
	if document.is_public:
		return
	if current_user and document.user_id == current_user.id:
		return
	raise HTTPException(status_code=403, detail="Access denied")


def _get_ppt_slide_or_404(document: PPTDocument, slide_number: int) -> Dict[str, Any]:
	slide = get_ppt_slide(document, slide_number)
	if not slide:
		raise HTTPException(status_code=404, detail="Slide not found")
	return slide


def _get_demo_html_or_400(slide: Dict[str, Any]) -> str:
	original_html = slide.get("demo_html")
	if not original_html:
		raise HTTPException(status_code=400, detail="No demo HTML found for this slide")
	return original_html


def _build_ppt_modification_status(slide: Dict[str, Any]) -> Dict[str, Any]:
	modification_status = slide.get("demo_modification_status", "not_started")

	if modification_status == "ready":
		return {
			"status": "ready",
			"message": "Modification completed",
			"modified_html": slide.get("modified_demo_html")
		}
	if modification_status == "error":
		return {
			"status": "error",
			"message": "Modification failed",
			"error": slide.get("demo_modification_error")
		}
	if modification_status == "processing":
		return {"status": "processing", "message": "Modification in progress"}

	return {"status": "not_started", "message": "No modification has been initiated"}


def _start_ppt_modification(
	request: "PPTEditRequest",
	document: PPTDocument,
	slide: Dict[str, Any],
	original_html: str,
	citations_dict: List[Dict[str, Any]],
	background_tasks: BackgroundTasks,
	db: Session
) -> "WebEditResponse":
	slide["demo_modification_status"] = "processing"
	slide["demo_modification_prompt"] = request.user_prompt
	slide["demo_modification_citations"] = citations_dict
	flag_modified(document, "slides_data")
	db.commit()

	# Create a fresh event so SSE streams can await completion
	_ppt_edit_events[(document.id, request.slide_number)] = asyncio.Event()

	background_tasks.add_task(
		modify_ppt_demo_with_citations_background,
		document.id,
		request.slide_number,
		original_html,
		citations_dict,
		request.user_prompt,
		request.thinking_enabled,
		request.model
	)

	return WebEditResponse(
		status="processing",
		message="PPT demo modification started. Poll the status endpoint to check progress."
	)


def _handle_ppt_keep_version(
	document: PPTDocument,
	slide: Dict[str, Any],
	version: str,
	db: Session
) -> Dict[str, Any]:
	if version == "after":
		modified_html = slide.get("modified_demo_html")
		if not modified_html:
			raise HTTPException(status_code=400, detail="No modified demo HTML found to save")
		slide["demo_html"] = modified_html
		document.user_prompt = slide.get("demo_modification_prompt")

	slide.pop("modified_demo_html", None)
	slide.pop("demo_modification_status", None)
	slide.pop("demo_modification_prompt", None)
	slide.pop("demo_modification_citations", None)
	slide.pop("demo_modification_error", None)
	flag_modified(document, "slides_data")
	db.commit()

	return {
		"status": "success",
		"message": f"Version '{version}' has been saved",
		"current_html": slide.get("demo_html")
	}


def _save_ppt_as_new_version(
	original_document: PPTDocument,
	slide: Dict[str, Any],
	slide_number: int,
	version: str,
	db: Session
) -> Dict[str, Any]:
	if version == "after":
		html_to_save = slide.get("modified_demo_html")
		if not html_to_save:
			raise HTTPException(status_code=400, detail="No modified demo HTML found to save")
	else:
		html_to_save = slide.get("demo_html")
		if not html_to_save:
			raise HTTPException(status_code=400, detail="No demo HTML found to save")

	root_id = original_document.root_document_id or original_document.id
	current_max_version = db.query(func.max(PPTDocument.version_number)).filter(
		or_(PPTDocument.root_document_id == root_id, PPTDocument.id == root_id)
	).scalar()
	new_version_number = (current_max_version or 0) + 1

	db.query(PPTDocument).filter(
		or_(PPTDocument.id == root_id, PPTDocument.root_document_id == root_id)
	).update({PPTDocument.is_current: 0}, synchronize_session=False)

	slides_data = copy.deepcopy(original_document.slides_data or {"slides": []})
	slides = slides_data.get("slides", [])
	target_slide = None
	for slide_item in slides:
		if slide_item.get("slide_number") == slide_number:
			target_slide = slide_item
			break

	if not target_slide:
		raise HTTPException(status_code=404, detail="Slide not found")

	target_slide["demo_html"] = html_to_save
	target_slide.pop("modified_demo_html", None)
	target_slide.pop("demo_modification_status", None)
	target_slide.pop("demo_modification_prompt", None)
	target_slide.pop("demo_modification_citations", None)
	target_slide.pop("demo_modification_error", None)

	new_document = PPTDocument(
		title=original_document.title,
		original_filename=original_document.original_filename,
		file_path=original_document.file_path,
		file_type=original_document.file_type,
		file_size=original_document.file_size,
		slide_count=original_document.slide_count,
		user_id=original_document.user_id,
		subject=original_document.subject,
		grade_level=original_document.grade_level,
		description=f"基于 '{original_document.title}' 编辑生成的版本 v{new_version_number}",
		is_public=original_document.is_public,
		status="ready",
		slides_data=slides_data,
		analysis_results=original_document.analysis_results,
		processing_config=original_document.processing_config,
		template_options=original_document.template_options,
		created_at=datetime.now(),
		updated_at=datetime.now(),
		root_document_id=root_id,
		version_number=new_version_number,
		is_current=1,
		user_prompt=slide.get("demo_modification_prompt")
	)

	db.add(new_document)
	db.commit()
	db.refresh(new_document)

	cleanup_old_ppt_versions(db, root_id, MAX_VERSION_HISTORY)

	return {
		"status": "success",
		"message": f"New PPT version created with version '{version}'",
		"new_document_id": new_document.id,
		"new_document_title": new_document.title,
		"version_number": new_version_number,
		"root_document_id": root_id,
		"current_html": html_to_save
	}


def _build_ppt_versions_response(document: PPTDocument, db: Session) -> Dict[str, Any]:
	root_id = document.root_document_id or document.id

	versions = db.query(PPTDocument).filter(
		or_(PPTDocument.id == root_id, PPTDocument.root_document_id == root_id)
	).order_by(PPTDocument.version_number.asc()).all()

	version_list = []
	for v in versions:
		version_list.append({
			"id": v.id,
			"title": v.title,
			"version_number": v.version_number,
			"is_current": v.is_current or 0,
			"is_root": v.id == root_id,
			"created_at": v.created_at.isoformat() if v.created_at else None,
			"description": v.description,
			"user_prompt": v.user_prompt,
		})

	return {
		"status": "success",
		"root_document_id": root_id,
		"total_versions": len(version_list),
		"max_versions": MAX_VERSION_HISTORY,
		"versions": version_list
	}


def _delete_ppt_version(
	root_document: PPTDocument,
	version_id: int,
	db: Session,
	log_prefix: str = ""
) -> Dict[str, Any]:
	root_id = root_document.root_document_id or root_document.id

	version_to_delete = db.query(PPTDocument).filter(PPTDocument.id == version_id).first()
	if not version_to_delete:
		raise HTTPException(status_code=404, detail="Version not found")

	version_root_id = version_to_delete.root_document_id or version_to_delete.id
	if version_root_id != root_id and version_to_delete.id != root_id:
		raise HTTPException(status_code=400, detail="Version does not belong to this document chain")

	if version_to_delete.id == root_id:
		has_children = db.query(PPTDocument).filter(PPTDocument.root_document_id == root_id).count()
		if has_children > 0:
			raise HTTPException(status_code=400, detail="Cannot delete root version with children")

	logger.info(f"🗑️ {log_prefix}Deleting PPT version {version_id} (v{version_to_delete.version_number}) from chain {root_id}".strip())
	db.delete(version_to_delete)
	db.commit()

	return {
		"status": "success",
		"message": f"Version {version_id} deleted successfully",
		"deleted_version_number": version_to_delete.version_number
	}


def _set_ppt_current_version_response(
	root_document: PPTDocument,
	version_id: int,
	db: Session
) -> Dict[str, Any]:
	root_id = root_document.root_document_id or root_document.id

	version_to_set = db.query(PPTDocument).filter(PPTDocument.id == version_id).first()
	if not version_to_set:
		raise HTTPException(status_code=404, detail="Version not found")

	version_root_id = version_to_set.root_document_id or version_to_set.id
	if version_root_id != root_id and version_to_set.id != root_id:
		raise HTTPException(status_code=400, detail="Version does not belong to this document chain")

	set_ppt_current_version(db, root_id, version_to_set.id)
	db.commit()

	return {
		"status": "success",
		"message": f"Version {version_id} set as current",
		"current_version_id": version_to_set.id
	}


def _upload_html_slide_impl(
	document: PPTDocument,
	html_str: str,
	filename: str,
	title: Optional[str],
	insert_after_index: Optional[int],
	db: Session
) -> Dict[str, Any]:
	# Extract title from HTML if not provided
	if not title:
		title_match = re.search(r'<title>(.*?)</title>', html_str, re.IGNORECASE)
		if title_match:
			title = title_match.group(1)
		else:
			title = filename.replace('.html', '')

	# Get slides data
	if not document.slides_data:
		document.slides_data = {"slides": []}

	slides = document.slides_data.get("slides", [])
	interactive_order = document.slides_data.get("interactive_order")

	# Initialize interactive_order if it doesn't exist
	if interactive_order is None:
		interactive_order = []
		for slide in slides:
			slide_number = slide.get("slide_number")
			if slide_number is None:
				continue
			if slide.get("is_html_upload"):
				continue
			interactive_order.append({"type": "slide", "slide_number": slide_number})
			if slide.get("needs_demo") and slide.get("demo_html"):
				interactive_order.append({"type": "demo", "slide_number": slide_number})
		logger.info(f"Initialized interactive_order with {len(interactive_order)} items from existing slides")

	# Determine the new slide number
	existing_numbers = [slide.get("slide_number", 0) for slide in slides]
	new_slide_number = max(existing_numbers) + 1 if existing_numbers else 1

	# Create new HTML slide item
	new_slide = {
		"slide_number": new_slide_number,
		"title": title,
		"description": f"上传: {filename}",
		"image_path": None,
		"needs_demo": False,
		"is_html_upload": True,
		"uploaded_html": html_str,
		"uploaded_filename": filename
	}

	slides.append(new_slide)

	# Insert into interactive_order
	new_order_item = {"type": "html_slide", "slide_number": new_slide_number}
	if insert_after_index is not None and 0 <= insert_after_index < len(interactive_order):
		insert_at_order_position = insert_after_index + 1
		interactive_order.insert(insert_at_order_position, new_order_item)
	else:
		interactive_order.append(new_order_item)

	# Update slides data
	document.slides_data["slides"] = slides
	document.slide_count = len(slides)
	document.slides_data["interactive_order"] = interactive_order

	flag_modified(document, "slides_data")
	db.commit()

	final_position = insert_after_index + 1 if insert_after_index is not None else len(interactive_order) - 1
	logger.info(f"✅ HTML file '{filename}' uploaded as slide {new_slide_number} in document {document.id} at interactive position {final_position}")

	return {
		"status": "success",
		"message": "HTML file uploaded successfully",
		"slide_number": new_slide_number,
		"title": title,
		"total_slides": len(slides),
		"document_id": document.id,
		"version_number": document.version_number
	}


def _get_current_ppt_version(
	requested_document: PPTDocument,
	db: Session,
	require_public: bool = False
) -> PPTDocument:
	"""Get the current version of a PPT document chain."""
	root_id = requested_document.root_document_id or requested_document.id

	query = db.query(PPTDocument).filter(
		PPTDocument.root_document_id == root_id,
		PPTDocument.is_current == 1
	)
	if require_public:
		query = query.filter(PPTDocument.is_public == True)

	document = query.first()

	if not document:
		query = db.query(PPTDocument).filter(PPTDocument.id == root_id)
		if require_public:
			query = query.filter(PPTDocument.is_public == True)
		document = query.first()

	if not document:
		raise HTTPException(status_code=404, detail="Current version not found")

	return document


def get_ppt_slide(document: PPTDocument, slide_number: int) -> Optional[Dict[str, Any]]:
	slides_data = document.slides_data or {}
	slides = slides_data.get("slides", [])
	for slide in slides:
		if slide.get("slide_number") == slide_number:
			return slide
	return None


def set_ppt_current_version(db: Session, root_id: int, current_id: int) -> None:
	db.query(PPTDocument).filter(
		or_(PPTDocument.id == root_id, PPTDocument.root_document_id == root_id)
	).update({PPTDocument.is_current: 0}, synchronize_session=False)
	db.query(PPTDocument).filter(PPTDocument.id == current_id).update(
		{PPTDocument.is_current: 1}, synchronize_session=False
	)


def cleanup_old_ppt_versions(db: Session, root_id: int, max_versions: int = MAX_VERSION_HISTORY) -> None:
	# Use bulk delete to avoid SQLAlchemy circular dependency issues when
	# removing older self-referential versions in the same transaction as new inserts.
	# Explicitly exclude root_id to prevent accidental deletion of the root document.
	versions = db.query(PPTDocument).filter(
		PPTDocument.root_document_id == root_id,
		PPTDocument.id != root_id
	).order_by(PPTDocument.created_at.asc()).all()

	total_count = len(versions) + 1
	excess_count = total_count - max_versions

	if excess_count > 0:
		old_version_ids = [v.id for v in versions[:excess_count]]
		if old_version_ids:
			db.query(PPTDocument).filter(PPTDocument.id.in_(old_version_ids)).delete(synchronize_session=False)
			db.commit()
			logger.info(f"✅ Cleaned up {excess_count} old PPT version(s) for root document {root_id}")


def _save_interactive_order_impl(document: PPTDocument, request: InteractiveOrderRequest, db: Session):
	"""Shared implementation for saving interactive order."""
	if not document.slides_data:
		raise HTTPException(status_code=404, detail="Slide data not found")

	slides = document.slides_data.get("slides", [])
	allowed_items = []
	allowed_keys = set()
	for slide in slides:
		slide_number = slide.get("slide_number")
		if slide_number is None:
			continue
		slide_key = ("slide", int(slide_number))
		allowed_items.append({"type": "slide", "slide_number": int(slide_number)})
		allowed_keys.add(slide_key)
		if slide.get("needs_demo") and slide.get("demo_html"):
			demo_key = ("demo", int(slide_number))
			allowed_items.append({"type": "demo", "slide_number": int(slide_number)})
			allowed_keys.add(demo_key)

	ordered_items = []
	seen = set()
	for item in request.order:
		item_type = "demo" if item.type == "demo" else "slide"
		item_key = (item_type, int(item.slide_number))
		if item_key in allowed_keys and item_key not in seen:
			ordered_items.append({"type": item_type, "slide_number": int(item.slide_number)})
			seen.add(item_key)

	for item in allowed_items:
		item_key = (item["type"], int(item["slide_number"]))
		if item_key not in seen:
			ordered_items.append(item)
			seen.add(item_key)

	document.slides_data["interactive_order"] = ordered_items
	flag_modified(document, "slides_data")
	db.commit()

	return {
		"status": "success",
		"total_items": len(ordered_items)
	}


@ppt_router.post("/documents/{document_id}/interactive-order")
async def save_interactive_order(
	document_id: int,
	request: InteractiveOrderRequest,
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db)
):
	document = db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
	if not document:
		raise HTTPException(status_code=404, detail="Document not found")

	if document.user_id != current_user.id:
		raise HTTPException(status_code=403, detail="Access denied")

	return _save_interactive_order_impl(document, request, db)


@ppt_router.post("/public/documents/{document_id}/interactive-order")
async def save_public_interactive_order(
	document_id: int,
	request: InteractiveOrderRequest,
	db: Session = Depends(get_db)
):
	document = db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
	if not document:
		raise HTTPException(status_code=404, detail="Document not found")

	if not document.is_public:
		raise HTTPException(status_code=403, detail="This document is not public")

	return _save_interactive_order_impl(document, request, db)


async def modify_ppt_demo_with_citations_background(
	document_id: int,
	slide_number: int,
	original_html: str,
	citations: List[Dict],
	user_prompt: str,
	thinking_enabled: Optional[bool] = None,
	model: Optional[str] = None
):
	logger.info(
		f"🔄 Starting PPT demo HTML modification for document {document_id}, slide {slide_number}"
	)
	logger.info(f"📦 Model: {model or 'default'}")
	start_time = time.time()

	background_db = SessionLocal()

	try:
		document = background_db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
		if not document:
			logger.error(f"❌ PPTDocument {document_id} not found")
			return

		slide = get_ppt_slide(document, slide_number)
		if not slide:
			logger.error(f"❌ Slide {slide_number} not found for document {document_id}")
			return

		editor_processor = get_editor_processor(model=model)
		result = await editor_processor.modify_html_with_citations(
			original_html=original_html,
			citations=citations,
			user_prompt=user_prompt,
			thinking_enabled=thinking_enabled
		)

		if result.get("status") == "error":
			logger.error(f"❌ PPT demo modification failed: {result.get('error')}")
			slide["demo_modification_status"] = "error"
			slide["demo_modification_error"] = result.get("error")
		else:
			modified_html = result.get("modified_html", original_html)
			slide["modified_demo_html"] = modified_html
			slide["demo_modification_status"] = "ready"
			slide["demo_modification_prompt"] = user_prompt
			slide["demo_modification_citations"] = citations

		flag_modified(document, "slides_data")
		background_db.commit()

		total_time = time.time() - start_time
		logger.info(f"🎉 PPT demo modification completed in {total_time:.2f}s")

	except Exception as e:
		logger.error(f"❌ PPT demo modification error: {str(e)}")
		try:
			document = background_db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
			if document:
				slide = get_ppt_slide(document, slide_number)
				if slide is not None:
					slide["demo_modification_status"] = "error"
					slide["demo_modification_error"] = str(e)
					flag_modified(document, "slides_data")
					background_db.commit()
		except Exception as db_error:
			logger.error(f"❌ Failed to update PPT demo error status: {str(db_error)}")

	finally:
		background_db.close()
		# Signal any waiting SSE streams that processing is done
		event = _ppt_edit_events.get((document_id, slide_number))
		if event:
			event.set()


@web_router.post("/ppt/edit", response_model=WebEditResponse)
@web_router.post("/public/ppt/edit", response_model=WebEditResponse)
async def edit_ppt_demo_html(
	background_tasks: BackgroundTasks,
	request: PPTEditRequest,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	logger.info(
		f"📝 Received PPT demo edit request for document {request.document_id}, slide {request.slide_number}"
	)
	logger.info(f"Citations: {request.citations} items, User prompt: {request.user_prompt}")

	document = _get_ppt_document_or_404(request.document_id, db)
	_ensure_ppt_access(document, current_user)

	slide = _get_ppt_slide_or_404(document, request.slide_number)
	original_html = _get_demo_html_or_400(slide)

	citations_dict = [c.dict() for c in request.citations]
	logger.info(f"{citations_dict} citations will be used for modification")

	return _start_ppt_modification(
		request=request,
		document=document,
		slide=slide,
		original_html=original_html,
		citations_dict=citations_dict,
		background_tasks=background_tasks,
		db=db
	)


@web_router.get("/ppt/edit/{document_id}/{slide_number}/stream")
@web_router.get("/public/ppt/edit/{document_id}/{slide_number}/stream")
async def stream_ppt_edit_status(
	document_id: int,
	slide_number: int,
	current_user: Optional[User] = Depends(get_optional_user_for_sse),
	db: Session = Depends(get_db)
):
	"""SSE endpoint: streams PPT slide edit status and pushes the final result the
	moment the background task finishes — no client-side polling required."""
	document = _get_ppt_document_or_404(document_id, db)
	_ensure_ppt_access(document, current_user)

	slide = _get_ppt_slide_or_404(document, slide_number)
	initial_status = _build_ppt_modification_status(slide)
	event = _ppt_edit_events.get((document_id, slide_number))

	async def generate():
		yield f"data: {json.dumps(initial_status)}\n\n"

		# Already finished — close immediately
		if initial_status["status"] in ("ready", "error"):
			return

		# No event registered means the task hasn't been started via this process
		if event is None:
			return

		# Wait for the background task to signal completion (max 15 minutes)
		try:
			await asyncio.wait_for(asyncio.shield(event.wait()), timeout=900)
		except asyncio.TimeoutError:
			yield f"data: {json.dumps({'status': 'timeout', 'message': 'Processing timed out'})}\n\n"
			return

		# Re-read the slide with a fresh session to get the committed result
		fresh_db = SessionLocal()
		try:
			doc = fresh_db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
			if doc:
				fresh_slide = get_ppt_slide(doc, slide_number)
				final_status = _build_ppt_modification_status(fresh_slide) if fresh_slide else {"status": "error", "message": "Slide not found"}
			else:
				final_status = {"status": "error", "message": "Document not found"}
			yield f"data: {json.dumps(final_status)}\n\n"
		finally:
			fresh_db.close()

	return StreamingResponse(
		generate(),
		media_type="text/event-stream",
		headers={
			"Cache-Control": "no-cache",
			"Connection": "keep-alive",
			"X-Accel-Buffering": "no",
		}
	)


@web_router.get("/ppt/edit/{document_id}/{slide_number}/status")
@web_router.get("/public/ppt/edit/{document_id}/{slide_number}/status")
async def get_ppt_edit_status(
	document_id: int,
	slide_number: int,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_ppt_document_or_404(document_id, db)
	_ensure_ppt_access(document, current_user)

	slide = _get_ppt_slide_or_404(document, slide_number)

	return _build_ppt_modification_status(slide)


@web_router.post("/ppt/edit/{document_id}/{slide_number}/keep-version")
@web_router.post("/public/ppt/edit/{document_id}/{slide_number}/keep-version")
async def keep_ppt_demo_version(
	document_id: int,
	slide_number: int,
	request: KeepVersionRequest,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_ppt_document_or_404(document_id, db)
	_ensure_ppt_access(document, current_user)

	slide = _get_ppt_slide_or_404(document, slide_number)

	return _handle_ppt_keep_version(document, slide, request.version, db)


@web_router.post("/ppt/edit/{document_id}/{slide_number}/save-as-new")
@web_router.post("/public/ppt/edit/{document_id}/{slide_number}/save-as-new")
async def save_ppt_demo_as_new_version(
	document_id: int,
	slide_number: int,
	request: KeepVersionRequest,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	original_document = _get_ppt_document_or_404(document_id, db)
	_ensure_ppt_access(original_document, current_user)

	slide = _get_ppt_slide_or_404(original_document, slide_number)

	return _save_ppt_as_new_version(original_document, slide, slide_number, request.version, db)


@ppt_router.get("/documents/{document_id}/versions")
@ppt_router.get("/public/documents/{document_id}/versions")
async def get_ppt_document_versions(
	document_id: int,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_ppt_document_or_404(document_id, db)
	_ensure_ppt_access(document, current_user)

	return _build_ppt_versions_response(document, db)


@ppt_router.delete("/documents/{document_id}/versions/{version_id}")
@ppt_router.delete("/public/documents/{document_id}/versions/{version_id}")
async def delete_ppt_document_version(
	document_id: int,
	version_id: int,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_ppt_document_or_404(document_id, db)
	_ensure_ppt_access(document, current_user)

	log_prefix = "Public " if document.is_public else ""
	return _delete_ppt_version(document, version_id, db, log_prefix=log_prefix)


@ppt_router.post("/documents/{document_id}/versions/{version_id}/set-current")
@ppt_router.post("/public/documents/{document_id}/versions/{version_id}/set-current")
async def set_ppt_current_version_endpoint(
	document_id: int,
	version_id: int,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_ppt_document_or_404(document_id, db)
	_ensure_ppt_access(document, current_user)

	return _set_ppt_current_version_response(document, version_id, db)


class HTMLUploadRequest(BaseModel):
	title: str
	insert_after_index: Optional[int] = None


@ppt_router.post("/documents/{document_id}/upload-html")
@ppt_router.post("/public/documents/{document_id}/upload-html")
async def upload_html_slide(
	document_id: int,
	file: UploadFile = File(...),
	title: Optional[str] = Form(None),
	insert_after_index: Optional[int] = Form(None),
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	"""
	Upload an HTML file and insert it as a new slide in the document.
	The HTML file title will be used for preview in the navigation.
	If the requested document is part of a version chain, the HTML will be
	uploaded to the current version of that chain.
	"""
	try:
		# First, find the requested document
		requested_document = _get_ppt_document_or_404(document_id, db)
		_ensure_ppt_access(requested_document, current_user)

		# If this document is part of a version chain, work on the current version
		require_public = requested_document.is_public and current_user is None
		document = _get_current_ppt_version(requested_document, db, require_public=require_public)

		# Verify access to the current version
		_ensure_ppt_access(document, current_user)

		# Log if we're modifying a different version than requested
		if document.id != document_id:
			logger.info(f"Uploading HTML to current version {document.id} (v{document.version_number}) instead of requested document {document_id}")

		# Validate file type
		if not file.filename or not file.filename.endswith('.html'):
			raise HTTPException(status_code=400, detail="Only HTML files are allowed")

		# Read HTML content
		html_content = await file.read()
		html_str = html_content.decode('utf-8')

		if insert_after_index is not None:
			logger.info(f"Upload: inserting HTML slide after interactive index {insert_after_index} in document {document_id}")
		else:
			logger.info(f"Upload: inserting HTML slide at the end of document {document_id}")

		return _upload_html_slide_impl(document, html_str, file.filename, title, insert_after_index, db)

	except HTTPException:
		raise
	except Exception as e:
		logger.error(f"Failed to upload HTML: {str(e)}")
		raise HTTPException(status_code=500, detail=f"Failed to upload HTML: {str(e)}")


