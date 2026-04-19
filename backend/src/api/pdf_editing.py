from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Form, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import Optional, Dict, Any, List
from pydantic import BaseModel
import asyncio
import json
import time
import logging
from datetime import datetime

from ..core.database import get_db, SessionLocal
from ..models.document import Document, MAX_VERSION_HISTORY
from ..models.user import User
from ..core.security import get_current_user, get_optional_user, get_optional_user_for_sse
from ..services.editor_processor import get_editor_processor
from ..services.ai_processor import AIProcessor
from ..api.pdf_processing import get_ai_processor
from sqlalchemy.orm.attributes import flag_modified

# In-process SSE event registry: document_id -> asyncio.Event
# Used to notify SSE stream endpoints the moment background editing completes.
_web_edit_events: Dict[int, asyncio.Event] = {}

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

web_router = APIRouter()
pdf_router = APIRouter()


class CitationItem(BaseModel):
	id: int
	index: int
	html: str
	selector: str
	note: Optional[str] = None


class WebEditRequest(BaseModel):
	document_id: int
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


class SaveAsNewVersionRequest(BaseModel):
	version: str  # 'before' | 'after'
	title_suffix: Optional[str] = None


async def modify_html_with_citations_background(
	document_id: int,
	original_html: str,
	citations: List[Dict],
	user_prompt: str,
	thinking_enabled: Optional[bool] = None,
	model: Optional[str] = None
):
	logger.info(f"🔄 Starting background HTML modification with citations for document {document_id}")
	logger.info(f"📦 Model: {model or 'default'}")
	start_time = time.time()

	background_db = SessionLocal()

	try:
		document = background_db.query(Document).filter(Document.id == document_id).first()
		if not document:
			logger.error(f"❌ Document {document_id} not found")
			return

		editor_processor = get_editor_processor(model=model)
		result = await editor_processor.modify_html_with_citations(
			original_html=original_html,
			citations=citations,
			user_prompt=user_prompt,
			thinking_enabled=thinking_enabled
		)

		if result.get("status") == "error":
			logger.error(f"❌ EditorProcessor modification failed: {result.get('error')}")
			document.error_message = result.get('error')
			if document.processing_results:
				document.processing_results['modified_website'] = original_html
				document.processing_results['modification_status'] = 'error'
				document.processing_results['modification_error'] = result.get('error')
				flag_modified(document, "processing_results")
		else:
			modified_html = result.get("modified_html", original_html)
			if document.processing_results:
				document.processing_results['modified_website'] = modified_html
				document.processing_results['modification_status'] = 'ready'
				document.processing_results['modification_prompt'] = user_prompt
				document.processing_results['modification_citations'] = citations
				flag_modified(document, "processing_results")
			logger.info(f"✅ Modified HTML stored for document {document_id}")

		background_db.commit()

		total_time = time.time() - start_time
		logger.info(f"🎉 Background HTML modification completed in {total_time:.2f}s")

	except Exception as e:
		logger.error(f"❌ Background modification error: {str(e)}")
		try:
			document = background_db.query(Document).filter(Document.id == document_id).first()
			if document and document.processing_results:
				document.processing_results['modification_status'] = 'error'
				document.processing_results['modification_error'] = str(e)
				flag_modified(document, "processing_results")
				background_db.commit()
		except Exception as db_error:
			logger.error(f"❌ Failed to update error status: {str(db_error)}")

	finally:
		background_db.close()
		# Signal any waiting SSE streams that processing is done
		event = _web_edit_events.get(document_id)
		if event:
			event.set()


async def modify_ui_background(
	new_document_id: int,
	original_html: str,
	user_prompt: str,
	document_context: Dict,
	db: Session
):
	logger.info(f"🔄 Starting background UI modification for document {new_document_id}")
	start_time = time.time()

	background_db = SessionLocal()

	try:
		new_document = background_db.query(Document).filter(Document.id == new_document_id).first()
		if not new_document:
			logger.error(f"❌ Document {new_document_id} not found")
			return

		ai_processor = get_ai_processor()
		logger.info("🤖 AI processor initialized for background UI modification")

		logger.info("🔄 Starting AI UI modification in background...")
		ai_processing_start = time.time()

		try:
			result = await ai_processor.modify_website_ui(
				original_html=original_html,
				user_prompt=user_prompt,
				document_context=document_context
			)

			if result["status"] == "error":
				new_document.status = "error"
				new_document.error_message = result.get("error", "UI modification failed")
			else:
				# Update processing_results with the modified HTML
				if new_document.processing_results is None:
					new_document.processing_results = {}
				new_document.processing_results["website"] = result.get("modified_html", original_html)
				new_document.status = "ready"
				new_document.user_prompt = user_prompt
				flag_modified(new_document, "processing_results")
				background_db.commit()
		except Exception as ai_error:
			logger.error(f"❌ AI UI modification failed: {str(ai_error)}")
			new_document.status = "error"
			new_document.error_message = str(ai_error)
			background_db.commit()

		total_time = time.time() - start_time
		logger.info(f"🎉 Background UI modification completed for document {new_document_id} in {total_time:.2f}s")

	except Exception as processing_error:
		logger.error(f"❌ Background UI modification error for document {new_document_id}: {str(processing_error)}")
		try:
			new_document = background_db.query(Document).filter(Document.id == new_document_id).first()
			if new_document:
				new_document.status = "error"
				new_document.error_message = str(processing_error)
				background_db.commit()
		except Exception as db_error:
			logger.error(f"❌ Failed to update error status: {str(db_error)}")

	finally:
		background_db.close()


def get_version_chain_count(db: Session, root_id: int) -> int:
	return db.query(Document).filter(
		or_(Document.root_document_id == root_id, Document.id == root_id)
	).count()


def cleanup_old_versions(db: Session, root_id: int, max_versions: int = MAX_VERSION_HISTORY):
	# Explicitly exclude root_id to prevent accidental deletion of the root document.
	versions = db.query(Document).filter(
		Document.root_document_id == root_id,
		Document.id != root_id
	).order_by(Document.created_at.asc()).all()

	total_count = len(versions) + 1
	excess_count = total_count - max_versions

	if excess_count > 0:
		for i in range(min(excess_count, len(versions))):
			db.delete(versions[i])
		db.commit()
		logger.info(f"✅ Cleaned up {excess_count} old version(s) for root document {root_id}")


def set_current_version(db: Session, root_id: int, current_id: int) -> None:
	db.query(Document).filter(
		or_(Document.id == root_id, Document.root_document_id == root_id)
	).update({Document.is_current: 0}, synchronize_session=False)
	db.query(Document).filter(Document.id == current_id).update(
		{Document.is_current: 1}, synchronize_session=False
	)


def _get_document_or_404(document_id: int, db: Session) -> Document:
	document = db.query(Document).filter(Document.id == document_id).first()
	if not document:
		raise HTTPException(status_code=404, detail="Document not found")
	return document


def _ensure_private_access(document: Document, current_user: User) -> None:
	if document.user_id != current_user.id and not document.is_public:
		raise HTTPException(status_code=403, detail="Access denied")


def _ensure_public_access(document: Document) -> None:
	if not document.is_public:
		raise HTTPException(status_code=403, detail="This document is not public")


def _ensure_owner_access(document: Document, current_user: User) -> None:
	if document.user_id != current_user.id:
		raise HTTPException(status_code=403, detail="Access denied")


def _ensure_access(document: Document, current_user: Optional[User]) -> None:
	"""Allow access if document is public OR user owns the document.

	- Private文档：必须有登录用户且为owner。
	- Public文档：匿名或任意用户均可访问。
	"""
	if document.is_public:
		return
	if current_user and document.user_id == current_user.id:
		return
	raise HTTPException(status_code=403, detail="Access denied")


def _get_original_html_or_400(document: Document) -> str:
	original_html = None
	if document.processing_results and document.processing_results.get('website'):
		original_html = document.processing_results['website']

	if not original_html:
		raise HTTPException(status_code=400, detail="No source HTML found for this document")

	return original_html


def _build_modification_status(processing_results: Optional[Dict[str, Any]]) -> Dict[str, Any]:
	if not processing_results:
		return {"status": "not_started", "message": "No modification has been initiated"}

	modification_status = processing_results.get('modification_status', 'not_started')

	if modification_status == 'ready':
		return {
			"status": "ready",
			"message": "Modification completed",
			"modified_html": processing_results.get('modified_website')
		}
	if modification_status == 'error':
		return {
			"status": "error",
			"message": "Modification failed",
			"error": processing_results.get('modification_error')
		}
	if modification_status == 'processing':
		return {"status": "processing", "message": "Modification in progress"}

	return {"status": "not_started", "message": "No modification has been initiated"}


def _start_modification(
	request: WebEditRequest,
	document: Document,
	original_html: str,
	citations_dict: List[Dict[str, Any]],
	background_tasks: BackgroundTasks,
	db: Session
) -> WebEditResponse:
	if document.processing_results:
		document.processing_results['modification_status'] = 'processing'
		document.user_prompt = request.user_prompt
		flag_modified(document, "processing_results")
		db.commit()

	# Create a fresh event so SSE streams can await completion
	_web_edit_events[document.id] = asyncio.Event()

	background_tasks.add_task(
		modify_html_with_citations_background,
		document.id,
		original_html,
		citations_dict,
		request.user_prompt,
		request.thinking_enabled,
		request.model
	)

	return WebEditResponse(
		status="processing",
		message="HTML modification started. Poll the status endpoint to check progress."
	)


def _handle_keep_version(document: Document, version: str, db: Session) -> Dict[str, Any]:
	if not document.processing_results:
		raise HTTPException(status_code=400, detail="No processing results found")

	if version == 'after':
		modified_html = document.processing_results.get('modified_website')
		if not modified_html:
			raise HTTPException(status_code=400, detail="No modified HTML found to save")
		document.processing_results['website'] = modified_html
		document.user_prompt = document.processing_results.get('modification_prompt')

	document.processing_results.pop('modified_website', None)
	document.processing_results.pop('modification_status', None)
	document.processing_results.pop('modification_prompt', None)
	document.processing_results.pop('modification_citations', None)
	document.processing_results.pop('modification_error', None)
	flag_modified(document, "processing_results")

	root_id = document.root_document_id or document.id
	set_current_version(db, root_id, document.id)
	db.commit()

	return {
		"status": "success",
		"message": f"Version '{version}' has been saved",
		"current_html": document.processing_results.get('website')
	}


def _build_versions_response(document: Document, db: Session) -> Dict[str, Any]:
	root_id = document.root_document_id or document.id

	versions = db.query(Document).filter(
		or_(Document.id == root_id, Document.root_document_id == root_id)
	).order_by(Document.version_number.asc()).all()

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


def _delete_version(
	root_document: Document,
	version_id: int,
	db: Session,
	log_prefix: str = ""
) -> Dict[str, Any]:
	root_id = root_document.root_document_id or root_document.id

	version_to_delete = db.query(Document).filter(Document.id == version_id).first()
	if not version_to_delete:
		raise HTTPException(status_code=404, detail="Version not found")

	version_root_id = version_to_delete.root_document_id or version_to_delete.id
	if version_root_id != root_id and version_to_delete.id != root_id:
		raise HTTPException(status_code=400, detail="Version does not belong to this document chain")

	if version_to_delete.id == root_id:
		has_children = db.query(Document).filter(Document.root_document_id == root_id).count()
		if has_children > 0:
			raise HTTPException(status_code=400, detail="Cannot delete root version with children")

	logger.info(f"🗑️ {log_prefix}Deleting version {version_id} (v{version_to_delete.version_number}) from chain {root_id}".strip())
	db.delete(version_to_delete)
	db.commit()

	return {
		"status": "success",
		"message": f"Version {version_id} deleted successfully",
		"deleted_version_number": version_to_delete.version_number
	}


def _set_current_version_response(root_document: Document, version_id: int, db: Session) -> Dict[str, Any]:
	root_id = root_document.root_document_id or root_document.id

	version_to_set = db.query(Document).filter(Document.id == version_id).first()
	if not version_to_set:
		raise HTTPException(status_code=404, detail="Version not found")

	version_root_id = version_to_set.root_document_id or version_to_set.id
	if version_root_id != root_id and version_to_set.id != root_id:
		raise HTTPException(status_code=400, detail="Version does not belong to this document chain")

	set_current_version(db, root_id, version_to_set.id)
	db.commit()

	return {
		"status": "success",
		"message": f"Version {version_id} set as current",
		"current_version_id": version_to_set.id
	}


@web_router.post("/edit", response_model=WebEditResponse)
@web_router.post("/public/edit", response_model=WebEditResponse)
async def edit_website_html(
	background_tasks: BackgroundTasks,
	request: WebEditRequest,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	logger.info(f"📝 Received web edit request for document {request.document_id}")

	document = _get_document_or_404(request.document_id, db)
	_ensure_access(document, current_user)

	original_html = _get_original_html_or_400(document)
	citations_dict = [c.dict() for c in request.citations]

	return _start_modification(
		request=request,
		document=document,
		original_html=original_html,
		citations_dict=citations_dict,
		background_tasks=background_tasks,
		db=db
	)


@web_router.get("/edit/{document_id}/stream")
@web_router.get("/public/edit/{document_id}/stream")
async def stream_edit_status(
	document_id: int,
	current_user: Optional[User] = Depends(get_optional_user_for_sse),
	db: Session = Depends(get_db)
):
	"""SSE endpoint: streams the edit status and pushes the final result the moment
	the background task finishes — no client-side polling required."""
	document = _get_document_or_404(document_id, db)
	_ensure_access(document, current_user)

	initial_status = _build_modification_status(document.processing_results)
	event = _web_edit_events.get(document_id)

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

		# Re-read the document with a fresh session to get the committed result
		fresh_db = SessionLocal()
		try:
			doc = fresh_db.query(Document).filter(Document.id == document_id).first()
			final_status = _build_modification_status(doc.processing_results if doc else None)
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


@web_router.get("/edit/{document_id}/status")
@web_router.get("/public/edit/{document_id}/status")
async def get_edit_status(
	document_id: int,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_document_or_404(document_id, db)
	_ensure_access(document, current_user)

	return _build_modification_status(document.processing_results)


@web_router.get("/edit/{document_id}/modified-html")
async def get_modified_html(
	document_id: int,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_document_or_404(document_id, db)
	_ensure_access(document, current_user)

	if not document.processing_results:
		raise HTTPException(status_code=400, detail="No processing results found")
	modified_html = document.processing_results.get('modified_website')
	if not modified_html:
		raise HTTPException(status_code=400, detail="No modified HTML found")
	return {"status": "success", "modified_html": modified_html}


@web_router.post("/edit/{document_id}/keep-version")
@web_router.post("/public/edit/{document_id}/keep-version")
async def keep_version(
	document_id: int,
	request: KeepVersionRequest,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_document_or_404(document_id, db)
	_ensure_access(document, current_user)

	return _handle_keep_version(document, request.version, db)


@web_router.post("/edit/{document_id}/save-as-new")
@web_router.post("/public/edit/{document_id}/save-as-new")
async def save_as_new_version(
	document_id: int,
	request: SaveAsNewVersionRequest,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	original_document = _get_document_or_404(document_id, db)
	_ensure_access(original_document, current_user)

	if not original_document.processing_results:
		raise HTTPException(status_code=400, detail="No processing results found")

	if request.version == 'after':
		html_to_save = original_document.processing_results.get('modified_website')
		if not html_to_save:
			raise HTTPException(status_code=400, detail="No modified HTML found to save")
	else:
		html_to_save = original_document.processing_results.get('website')
		if not html_to_save:
			raise HTTPException(status_code=400, detail="No HTML found to save")

	root_id = original_document.root_document_id or original_document.id
	current_max_version = db.query(func.max(Document.version_number)).filter(
		or_(Document.root_document_id == root_id, Document.id == root_id)
	).scalar()
	new_version_number = (current_max_version or 0) + 1

	db.query(Document).filter(
		or_(Document.id == root_id, Document.root_document_id == root_id)
	).update({Document.is_current: 0}, synchronize_session=False)

	title_suffix = (request.title_suffix or '').strip()
	new_title = f"{original_document.title} {title_suffix}".strip() if title_suffix else original_document.title

	new_processing_results = {
		'website': html_to_save,
		'analysis': original_document.processing_results.get('analysis'),
		'interactive_elements': original_document.processing_results.get('interactive_elements'),
	}

	new_document = Document(
		title=new_title,
		original_filename=original_document.original_filename,
		file_path=original_document.file_path,
		file_size=original_document.file_size,
		page_count=original_document.page_count,
		subject=original_document.subject,
		grade_level=original_document.grade_level,
		description=f"基于 '{original_document.title}' 编辑生成的版本 v{new_version_number}",
		user_id=original_document.user_id,
		is_public=True,
		status="ready",
		pdf_metadata=original_document.pdf_metadata,
		processing_results=new_processing_results,
		created_at=datetime.now(),
		updated_at=datetime.now(),
		root_document_id=root_id,
		version_number=new_version_number,
		is_current=1,
		user_prompt=original_document.processing_results.get('modification_prompt'),
	)

	db.add(new_document)
	db.commit()
	db.refresh(new_document)

	cleanup_old_versions(db, root_id, MAX_VERSION_HISTORY)

	original_document.processing_results.pop('modified_website', None)
	original_document.processing_results.pop('modification_status', None)
	original_document.processing_results.pop('modification_prompt', None)
	original_document.processing_results.pop('modification_citations', None)
	original_document.processing_results.pop('modification_error', None)
	original_document.user_prompt = None
	flag_modified(original_document, "processing_results")
	db.commit()

	return {
		"status": "success",
		"message": f"New document created with version '{request.version}'",
		"new_document_id": new_document.id,
		"new_document_title": new_document.title,
		"version_number": new_version_number,
		"root_document_id": root_id,
		"current_html": html_to_save
	}


@web_router.get("/documents/{document_id}/versions")
@web_router.get("/public/documents/{document_id}/versions")
async def get_document_versions(
	document_id: int,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_document_or_404(document_id, db)
	_ensure_access(document, current_user)

	return _build_versions_response(document, db)


@web_router.delete("/documents/{document_id}/versions/{version_id}")
@web_router.delete("/public/documents/{document_id}/versions/{version_id}")
async def delete_document_version(
	document_id: int,
	version_id: int,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_document_or_404(document_id, db)
	_ensure_access(document, current_user)

	log_prefix = "Public " if document.is_public else ""
	return _delete_version(document, version_id, db, log_prefix=log_prefix)


@web_router.post("/documents/{document_id}/versions/{version_id}/set-current")
@web_router.post("/public/documents/{document_id}/versions/{version_id}/set-current")
async def set_current_version_route(
	document_id: int,
	version_id: int,
	current_user: Optional[User] = Depends(get_optional_user),
	db: Session = Depends(get_db)
):
	document = _get_document_or_404(document_id, db)
	_ensure_access(document, current_user)

	return _set_current_version_response(document, version_id, db)


@pdf_router.post("/documents/{document_id}/modify-ui")
async def modify_document_ui(
	background_tasks: BackgroundTasks,
	document_id: int,
	prompt: str = Form(...),
	is_public: bool = Form(False),
	current_user: User = Depends(get_current_user),
	db: Session = Depends(get_db)
):
	start_time = time.time()
	logger.info(f"🎨 Starting UI modification for document {document_id}")

	document = db.query(Document).filter(Document.id == document_id).first()
	if not document:
		raise HTTPException(status_code=404, detail="Document not found")

	if document.user_id != current_user.id and not document.is_public:
		raise HTTPException(status_code=403, detail="Access denied")

	if not document.processing_results or not document.processing_results.get("website"):
		raise HTTPException(status_code=400, detail="No website HTML found for this document")

	original_html = document.processing_results.get("website")

	root_id = document.root_document_id or document.id
	current_max_version = db.query(func.max(Document.version_number)).filter(
		or_(Document.root_document_id == root_id, Document.id == root_id)
	).scalar()
	new_version_number = (current_max_version or 0) + 1

	db.query(Document).filter(
		or_(Document.id == root_id, Document.root_document_id == root_id)
	).update({Document.is_current: 0}, synchronize_session=False)

	new_document = Document(
		title=document.title,
		original_filename=document.original_filename,
		file_path=document.file_path,
		file_size=document.file_size,
		page_count=document.page_count,
		subject=document.subject,
		grade_level=document.grade_level,
		description=document.description,
		user_id=document.user_id,
		is_public=is_public,
		status="processing",
		pdf_metadata=document.pdf_metadata,
		processing_results=document.processing_results,
		created_at=datetime.now(),
		updated_at=datetime.now(),
		root_document_id=root_id,
		version_number=new_version_number,
		is_current=1,
		user_prompt=prompt,
	)

	db.add(new_document)
	db.commit()
	db.refresh(new_document)

	document_context = {
		"title": document.title,
		"subject": document.subject,
		"grade_level": document.grade_level,
		"description": document.description,
	}

	background_tasks.add_task(
		modify_ui_background,
		new_document.id,
		original_html,
		prompt,
		document_context,
		db
	)

	total_time = time.time() - start_time
	logger.info(f"✅ UI modification task queued in {total_time:.2f}s")

	return {
		"status": "processing",
		"message": "UI modification started. Poll status to check progress.",
		"document_id": new_document.id,
		"version_number": new_version_number,
		"root_document_id": root_id
	}
