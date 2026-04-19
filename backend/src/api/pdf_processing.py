from fastapi import APIRouter, File, UploadFile, HTTPException, Depends, Form, BackgroundTasks
from fastapi.responses import JSONResponse, FileResponse
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any, List
import os
import uuid
import json
import time
import logging
from pathlib import Path

from ..core.database import get_db, SessionLocal
from ..models.document import Document
from ..models.user import User
from ..services.ai_processor import AIProcessor
from ..core.security import get_current_user

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

router = APIRouter()

# Model to provider mapping
CHINESE_MODELS = ["claude-sonnet-4-6", "claude-opus-4-6", "claude-haiku-4-5-20251001",
                  "glm-4.7", "glm-4.6", "glm-4.6v"]


def get_provider_for_model(model: str) -> str:
    """
    Determine the provider type based on the model name.

    Args:
        model: Model name

    Returns:
        Provider type: "chinese" or "english"
    """
    if model in CHINESE_MODELS:
        return "chinese"
    return "english"


# Initialize AI processor with configurable provider
def get_ai_processor(generation_mode: str = "fast", ai_model: Optional[str] = None):
    """
    Get AI processor instance based on configuration.

    Args:
        generation_mode: HTML generation mode ("fast" or "heavy")
        ai_model: Specific model to use. If provided, provider is inferred from model name.

    Returns:
        AIProcessor instance
    """
    # If a specific model is provided, infer provider from model
    if ai_model:
        provider_type = get_provider_for_model(ai_model)
        logger.info(f"Using model {ai_model} with inferred provider: {provider_type}")
    else:
        provider_type = os.getenv('AI_PROVIDER', 'chinese').lower()

    # Set model and API key based on provider type
    if provider_type in ['english', 'gemini', 'openai']:
        if provider_type == 'gemini':
            model = ai_model or os.getenv('GEMINI_MODEL', 'gemini-3-pro-image-preview')
            api_key = os.getenv('GEMINI_API_KEY') or os.getenv('ENGLISH_API_KEY') or os.getenv('MIDDLE_TRANSFER_API_KEY')
        elif provider_type == 'openai':
            model = ai_model or os.getenv('OPENAI_MODEL', 'gpt-4.1')
            api_key = os.getenv('OPENAI_API_KEY') or os.getenv('ENGLISH_API_KEY') or os.getenv('MIDDLE_TRANSFER_API_KEY')
        else:  # english (default)
            model = ai_model or os.getenv('ENGLISH_MODEL', 'gpt-4.1')
            api_key = os.getenv('ENGLISH_API_KEY') or os.getenv('MIDDLE_TRANSFER_API_KEY') or os.getenv('OPENAI_API_KEY') or os.getenv('GEMINI_API_KEY')

        provider_config = {
            'provider': 'english',  # Always use unified English provider
            'model': model,
            'api_key': api_key
        }
    elif provider_type == 'chinese':
        # Unified Chinese provider - auto-detect backend from model name
        # For vision tasks, prefer glm-4.6v; for text generation, use specified model
        if ai_model and ai_model.startswith('claude-'):
            # Anthropic model
            model = ai_model
            api_key = os.getenv('ANTHROPIC_API_KEY')
            base_url = os.getenv('ANTHROPIC_BASE_URL')
        else:
            # Zhipu model (default)
            model = 'glm-4.6v'  # Vision model for PDF processing
            api_key = os.getenv('ZHIPU_API_KEY')
            base_url = None

        text_model = ai_model if ai_model in CHINESE_MODELS else os.getenv('ZHIPU_MODEL', 'glm-4.7')
        provider_config = {
            'provider': 'chinese',
            'model': model,
            'api_key': api_key,
            'base_url': base_url,
            'text_model': text_model
        }
    else:
        raise ValueError(f"Unsupported provider: {provider_type}. Supported providers: english, chinese")

    return AIProcessor(provider_config=provider_config, generation_mode=generation_mode)

# Ensure uploads directory exists
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

async def process_pdf_background(
    document_id: int,
    file_path: str,
    user_prefs: Dict,
    db: Session,
    generation_mode: str = "fast"
):
    """
    Background task to process PDF asynchronously.
    This runs in the background and doesn't block the API endpoint.

    Args:
        document_id: Database ID of the document
        file_path: Path to the PDF file
        user_prefs: User preferences dict
        db: Database session
        generation_mode: HTML generation mode ("fast" or "heavy")
    """
    logger.info(f"🔄 Starting background PDF processing for document {document_id}")
    start_time = time.time()

    # Create a new database session for this background task
    from ..core.database import SessionLocal
    background_db = SessionLocal()

    try:
        # Get the document
        document = background_db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"❌ Document {document_id} not found for background processing")
            return

        # Get AI model from user preferences
        ai_model = user_prefs.get("ai_model")

        # Get AI processor instance with the selected model
        ai_processor = get_ai_processor(generation_mode=generation_mode, ai_model=ai_model)
        logger.info(f"🤖 AI processor initialized for background processing - Provider: {ai_processor.get_provider_name()}, Mode: {generation_mode}, Model: {ai_model}")

        # Process PDF with configured AI provider
        logger.info(f"🔄 Starting AI processing pipeline in background...")
        ai_processing_start = time.time()
        result = await ai_processor.process_pdf_complete(
            str(file_path),
            user_preferences=user_prefs
        )
        ai_processing_time = time.time() - ai_processing_start
        logger.info(f"✅ Background AI processing completed in {ai_processing_time:.2f}s")

        if result["status"] == "error":
            logger.error(f"❌ Background processing failed: {result['error']}")
            document.status = "error"
            document.error_message = result['error']
        else:
            # Update document with processing results
            document.status = "ready"
            document.page_count = result["metadata"].get("page_count", 0)
            document.pdf_metadata = result["metadata"]
            document.processing_results = {
                "analysis": result["analysis"],
                "knowledge_cards": result.get("knowledge_cards", {}),
                "website": result["website"]["html"],
                "interactive_elements": result["website"]["interactive_elements"],
                "processing_info": result["processing_info"],
                "generation_mode": result["website"].get("mode_used", generation_mode)
            }
            logger.info(f"✅ Document {document_id} marked as ready with generation_mode: {result['website'].get('mode_used', generation_mode)}")
            logger.info(f"✅ Document {document_id} marked as ready")

        background_db.commit()

        total_time = time.time() - start_time
        logger.info(f"🎉 Background PDF processing completed for document {document_id} in {total_time:.2f}s total")

    except Exception as processing_error:
        logger.error(f"❌ Background processing error for document {document_id}: {str(processing_error)}")
        # Update document status to error
        try:
            document = background_db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.error_message = str(processing_error)
                background_db.commit()
        except Exception as db_error:
            logger.error(f"❌ Failed to update error status: {str(db_error)}")

    finally:
        # Always close the database session
        background_db.close()

async def process_concept_background(
    document_id: int,
    concept_data: Dict,
    user_prefs: Dict,
    db: Session
):
    """
    Background task to process concept asynchronously.
    This runs in the background and doesn't block the API endpoint.
    """
    logger.info(f"🔄 Starting background concept processing for document {document_id}")
    start_time = time.time()

    # Create a new database session for this background task
    from ..core.database import SessionLocal
    background_db = SessionLocal()

    try:
        # Get the document
        document = background_db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"❌ Document {document_id} not found for background concept processing")
            return

        # Get AI model from user preferences
        ai_model = user_prefs.get("ai_model")

        # Get AI processor instance with the selected model
        ai_processor = get_ai_processor(ai_model=ai_model)
        logger.info(f"🤖 AI processor initialized for background concept processing - Provider: {ai_processor.get_provider_name()}, Model: {ai_model}")

        # Process concept with configured AI provider
        logger.info(f"🔄 Starting AI concept processing in background...")
        ai_processing_start = time.time()
        result = await ai_processor.process_concept_complete(
            concept_data=concept_data,
            user_preferences=user_prefs
        )
        ai_processing_time = time.time() - ai_processing_start
        logger.info(f"✅ Background AI concept processing completed in {ai_processing_time:.2f}s")

        if result["status"] == "error":
            logger.error(f"❌ Background concept processing failed: {result['error']}")
            document.status = "error"
            document.error_message = result['error']
        else:
            # Update document with processing results
            document.status = "ready"
            document.page_count = result["metadata"].get("page_count", 1)
            document.pdf_metadata = result["metadata"]
            document.processing_results = {
                "analysis": result["analysis"],
                "website": result["website"]["html"],
                "interactive_elements": result["website"].get("interactive_elements", []),
                "processing_info": result["processing_info"],
                "concept_data": result["processing_info"].get("concept_data", {})
            }
            logger.info(f"✅ Document {document_id} marked as ready")

        background_db.commit()

        total_time = time.time() - start_time
        logger.info(f"🎉 Background concept processing completed for document {document_id} in {total_time:.2f}s total")

    except Exception as processing_error:
        logger.error(f"❌ Background concept processing error for document {document_id}: {str(processing_error)}")
        # Update document status to error
        try:
            document = background_db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.error_message = str(processing_error)
                background_db.commit()
        except Exception as db_error:
            logger.error(f"❌ Failed to update error status: {str(db_error)}")

    finally:
        # Always close the database session
        background_db.close()


@router.post("/upload")
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    subject: Optional[str] = Form(None),
    grade_level: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    user_preferences: Optional[str] = Form(None),
    generation_mode: str = Form("fast"),
    ai_model: Optional[str] = Form(None),
    zhipu_text_model: Optional[str] = Form(None),  # Kept for backward compatibility
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload and process a PDF file using AI to convert it into an interactive learning website.
    Processing happens in the background, so the endpoint returns immediately.

    Generation Modes:
    - fast: Quick generation (~30 seconds) using one-shot prompting
    - heavy: High-quality generation (~3-5 minutes) using 4-stage pipeline with validation
    - auto: Use system default (currently "fast")
    """
    start_time = time.time()
    logger.info(f"🚀 Starting PDF upload process for file: {file.filename}")

    try:
        # Validate file type
        if not file.content_type == "application/pdf":
            raise HTTPException(status_code=400, detail="Only PDF files are allowed")

        # Generate unique filename
        file_extension = os.path.splitext(file.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        file_path = UPLOAD_DIR / unique_filename

        # Save uploaded file
        file_save_start = time.time()
        with open(file_path, "wb") as buffer:
            content = await file.read()
            buffer.write(content)
        file_save_time = time.time() - file_save_start
        logger.info(f"📁 File saved in {file_save_time:.2f}s - Size: {len(content)/1024/1024:.2f}MB")

        # Parse user preferences if provided
        user_prefs = {}
        if user_preferences:
            try:
                user_prefs = json.loads(user_preferences)
            except json.JSONDecodeError:
                user_prefs = {}

        # Add grade level from form if provided
        if grade_level:
            user_prefs["grade_level"] = grade_level

        # Add description from form if provided
        if description:
            user_prefs["description"] = description

        # Add AI model - prefer ai_model, fallback to zhipu_text_model for backward compatibility
        selected_model = ai_model or zhipu_text_model
        if selected_model:
            user_prefs["ai_model"] = selected_model
            # Also set zhipu_text_model for backward compatibility with ZhipuProvider
            if selected_model.startswith("glm-"):
                user_prefs["zhipu_text_model"] = selected_model

        # Create document record with "processing" status
        db_start = time.time()
        document = Document(
            title=title,
            original_filename=file.filename,
            file_path=str(file_path),
            file_size=len(content),
            user_id=current_user.id,
            subject=subject,
            grade_level=grade_level,
            description=description,
            is_public=is_public,
            status="processing"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        db_time = time.time() - db_start
        logger.info(f"🗃️ Database record created in {db_time:.2f}s - Document ID: {document.id}")

        # Add background task to process the PDF
        background_tasks.add_task(
            process_pdf_background,
            document_id=document.id,
            file_path=str(file_path),
            user_prefs=user_prefs,
            db=db,
            generation_mode=generation_mode
        )

        total_time = time.time() - start_time
        logger.info(f"✅ PDF upload endpoint completed in {total_time:.2f}s - Processing continues in background")

        # Return immediately with document info
        result = {
            "id": document.id,
            "title": document.title,
            "original_filename": document.original_filename,
            "subject": document.subject,
            "grade_level": document.grade_level,
            "status": "processing",
            "message": "PDF uploaded successfully. Processing is happening in the background. Use the /documents/{id}/processing-status endpoint to check progress.",
            "created_at": document.created_at
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.get("/documents")
async def get_documents(
    skip: int = 0,
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of user's processed PDF documents with version information.
    Returns aggregated root documents with version counts.
    """
    try:
        # Get all documents for the user
        all_documents = db.query(Document).filter(
            Document.user_id == current_user.id
        ).all()

        # Group documents by root_document_id
        grouped_docs = {}
        for doc in all_documents:
            root_id = doc.root_document_id or doc.id
            if root_id not in grouped_docs:
                grouped_docs[root_id] = []
            grouped_docs[root_id].append(doc)

        # For each group, return the current version (or root if no current)
        result = []
        for root_id, doc_group in grouped_docs.items():
            # Find current version
            current_doc = next((d for d in doc_group if d.is_current == 1), None)
            # If no current version, use the root document or latest version
            if not current_doc:
                current_doc = next((d for d in doc_group if d.root_document_id is None), doc_group[-1])
            
            version_count = len(doc_group)
            
            result.append({
                "id": current_doc.id,
                "title": current_doc.title,
                "original_filename": current_doc.original_filename,
                "page_count": current_doc.page_count,
                "subject": current_doc.subject,
                "grade_level": current_doc.grade_level,
                "status": current_doc.status,
                "created_at": current_doc.created_at,
                "updated_at": current_doc.updated_at,
                "root_document_id": current_doc.root_document_id,
                "version_number": current_doc.version_number,
                "is_current": current_doc.is_current,
                "version_count": version_count,
                "user_prompt": current_doc.user_prompt
            })

        # Sort by created_at descending
        result.sort(key=lambda x: x["created_at"], reverse=True)
        
        # Apply pagination
        paginated_result = result[skip:skip + limit] if limit > 0 else result[skip:]

        return paginated_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch documents: {str(e)}")

@router.get("/documents/{document_id}")
async def get_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get specific document details including generated website.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        result = {
            "id": document.id,
            "title": document.title,
            "original_filename": document.original_filename,
            "page_count": document.page_count,
            "subject": document.subject,
            "grade_level": document.grade_level,
            "description": document.description,
            "status": document.status,
            "pdf_metadata": document.pdf_metadata,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }

        # Include processing results if available
        if document.processing_results:
            result["website"] = document.processing_results.get("website")
            result["analysis"] = document.processing_results.get("analysis")
            result["knowledge_cards"] = document.processing_results.get("knowledge_cards")
            result["interactive_elements"] = document.processing_results.get("interactive_elements")
            result["processing_info"] = document.processing_results.get("processing_info")
            result["generation_mode"] = document.processing_results.get("generation_mode")

            # Get concept_data from either processing_results or processing_info
            concept_data = document.processing_results.get("concept_data")
            if not concept_data:
                # Fallback to processing_info.concept_data for backward compatibility
                processing_info = document.processing_results.get("processing_info", {})
                concept_data = processing_info.get("concept_data")
            result["concept_data"] = concept_data

        if document.error_message:
            result["error_message"] = document.error_message

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document: {str(e)}")

@router.get("/documents/{document_id}/processing-status")
async def get_processing_status(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get processing status of a document.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        progress = 100 if document.status == "ready" else (50 if document.status == "processing" else 0)
        message = "Processing complete" if document.status == "ready" else \
                 ("Processing PDF..." if document.status == "processing" else "Error occurred")

        if document.error_message:
            message = f"Error: {document.error_message}"

        return {
            "document_id": document.id,
            "status": document.status,
            "progress": progress,
            "message": message
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch processing status: {str(e)}")

@router.get("/documents/{document_id}/website")
async def get_generated_website(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get the generated interactive website for a document.
    Returns the HTML content directly.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if document.status != "ready":
            raise HTTPException(status_code=400, detail="Document not ready or processing failed")

        if not document.processing_results or not document.processing_results.get("website"):
            raise HTTPException(status_code=404, detail="Website content not found")

        return JSONResponse({
            "html": document.processing_results["website"],
            "metadata": {
                "title": document.title,
                "subject": document.subject,
                "grade_level": document.grade_level
            }
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch website: {str(e)}")

@router.get("/public/documents/{document_id}")
async def get_public_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get specific document details including generated website for public access.
    Only works for documents that are marked as public.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_public == True
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Public document not found")

        result = {
            "id": document.id,
            "title": document.title,
            "original_filename": document.original_filename,
            "page_count": document.page_count,
            "subject": document.subject,
            "grade_level": document.grade_level,
            "description": document.description,
            "status": document.status,
            "pdf_metadata": document.pdf_metadata,
            "created_at": document.created_at,
            "updated_at": document.updated_at
        }

        # Include processing results if available
        if document.processing_results:
            result["website"] = document.processing_results.get("website")
            result["analysis"] = document.processing_results.get("analysis")
            result["knowledge_cards"] = document.processing_results.get("knowledge_cards")
            result["interactive_elements"] = document.processing_results.get("interactive_elements")
            result["processing_info"] = document.processing_results.get("processing_info")
            result["generation_mode"] = document.processing_results.get("generation_mode")

            # Get concept_data from either processing_results or processing_info
            concept_data = document.processing_results.get("concept_data")
            if not concept_data:
                # Fallback to processing_info.concept_data for backward compatibility
                processing_info = document.processing_results.get("processing_info", {})
                concept_data = processing_info.get("concept_data")
            result["concept_data"] = concept_data

        if document.error_message:
            result["error_message"] = document.error_message

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch public document: {str(e)}")

@router.get("/public/documents/{document_id}/view/{version_id}")
async def get_public_document_view_by_version(
    document_id: int,
    version_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the website HTML content for direct viewing of a specific version of a public document.
    Returns only the website HTML for rendering in a clean view.

    Path Parameters:
        document_id: The root document ID (used for grouping versions)
        version_id: The version number to view 
    """
    try:
        # Get the specific version by version_id (which is the document id)
        # Verify it's public and belongs to the document chain
        version_document = db.query(Document).filter(
            Document.version_number == version_id,
            Document.is_public == True,
            (Document.root_document_id == document_id) | (Document.id == document_id)
        ).first()

        if not version_document:
            raise HTTPException(status_code=404, detail="Document version not found")

        if not version_document.processing_results:
            raise HTTPException(status_code=404, detail="Document content not found")

        website_html = version_document.processing_results.get("website")

        if not website_html:
            raise HTTPException(status_code=404, detail="Website content not available")

        return {
            "id": version_document.id,
            "title": version_document.title,
            "version_number": version_document.version_number,
            "website_html": website_html
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document version view: {str(e)}")


@router.get("/public/documents/{document_id}/view")
async def get_public_document_view(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get the website HTML content for direct viewing of a public document.
    Returns only the website HTML for rendering in a clean view.
    If document_id is a root document, returns the current version (is_current=1).
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_public == True
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Public document not found")

        # If this is a root document (root_document_id is None), find the current version
        if document.root_document_id is None:
            current_version = db.query(Document).filter(
                Document.root_document_id == document_id,
                Document.is_current == 1,
                Document.is_public == True
            ).first()
            if current_version:
                document = current_version

        if not document.processing_results:
            raise HTTPException(status_code=404, detail="Document content not found")

        website_html = document.processing_results.get("website")

        if not website_html:
            raise HTTPException(status_code=404, detail="Website content not available")

        return {
            "id": document.id,
            "title": document.title,
            "website_html": website_html
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch document view: {str(e)}")

@router.get("/public/documents/{document_id}/processing-status")
async def get_public_processing_status(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Get processing status of a public document.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_public == True
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Public document not found")

        progress = 100 if document.status == "ready" else (50 if document.status == "processing" else 0)
        message = "Processing complete" if document.status == "ready" else \
                 ("Processing PDF..." if document.status == "processing" else "Error occurred")

        if document.error_message:
            message = f"Error: {document.error_message}"

        return {
            "document_id": document.id,
            "status": document.status,
            "progress": progress,
            "message": message
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch public processing status: {str(e)}")

@router.get("/public/documents/{document_id}/download")
async def download_public_document(
    document_id: int,
    db: Session = Depends(get_db)
):
    """
    Download the original PDF file for a public document.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.is_public == True
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Public document not found")

        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")

        # Return the file with appropriate headers for download
        return FileResponse(
            path=document.file_path,
            filename=document.original_filename,
            media_type='application/pdf'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download public document: {str(e)}")

@router.get("/public/documents")
async def get_public_documents(
    skip: int = 0,
    limit: int = 20,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get list of all public documents for public browsing.
    Optional date filtering: date_from and date_to should be in YYYY-MM-DD format.
    """
    try:
        query = db.query(Document).filter(
            Document.is_public == True,
            Document.status == "ready"
        )

        # Apply date filtering if provided
        if date_from:
            try:
                from datetime import datetime
                date_from_dt = datetime.strptime(date_from, "%Y-%m-%d")
                query = query.filter(Document.created_at >= date_from_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_from format. Use YYYY-MM-DD")

        if date_to:
            try:
                from datetime import datetime
                date_to_dt = datetime.strptime(date_to, "%Y-%m-%d")
                # Add one day to make it inclusive of the end date
                from datetime import timedelta
                date_to_dt = date_to_dt + timedelta(days=1)
                query = query.filter(Document.created_at < date_to_dt)
            except ValueError:
                raise HTTPException(status_code=400, detail="Invalid date_to format. Use YYYY-MM-DD")

        # Order by creation date (newest first)
        query = query.order_by(Document.created_at.desc())

        documents = query.offset(skip).limit(limit).all()

        return [
            {
                "id": doc.id,
                "title": doc.title,
                "original_filename": doc.original_filename,
                "page_count": doc.page_count,
                "subject": doc.subject,
                "grade_level": doc.grade_level,
                "description": doc.description,
                "status": doc.status,
                "created_at": doc.created_at,
                "updated_at": doc.updated_at,
                # Version management fields
                "root_document_id": doc.root_document_id,
                "version_number": doc.version_number or 1,
                "is_current": doc.is_current or 0,
                "user_prompt": doc.user_prompt
            }
            for doc in documents
        ]

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch public documents: {str(e)}")

@router.get("/documents/{document_id}/download")
async def download_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download the original PDF file for a document.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        if not os.path.exists(document.file_path):
            raise HTTPException(status_code=404, detail="PDF file not found")

        # Return the file with appropriate headers for download
        return FileResponse(
            path=document.file_path,
            filename=document.original_filename,
            media_type='application/pdf'
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to download document: {str(e)}")


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a document and all versions in the same version chain.
    Also removes associated files from the filesystem when present.
    """
    try:
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Delete the whole version chain so dashboard cards and DB stay in sync.
        root_id = document.root_document_id or document.id
        chain_documents = db.query(Document).filter(
            Document.user_id == current_user.id,
            (Document.id == root_id) | (Document.root_document_id == root_id)
        ).all()

        if not chain_documents:
            chain_documents = [document]

        deleted_document_ids: List[int] = []

        # Delete files from filesystem first (if the document has a stored file path)
        for doc in chain_documents:
            if doc.file_path and os.path.exists(doc.file_path):
                os.remove(doc.file_path)
            deleted_document_ids.append(doc.id)

        # Delete from database
        for doc in chain_documents:
            db.delete(doc)
        db.commit()

        return {
            "message": "Document deleted successfully",
            "deleted_document_ids": deleted_document_ids,
            "deleted_count": len(deleted_document_ids),
            "deleted_root_document_id": root_id
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")

@router.post("/concept/upload")
async def upload_concept(
    background_tasks: BackgroundTasks,
    subject: str = Form(...),
    concept_name: str = Form(...),
    concept_overview: str = Form(...),
    mastery_points: str = Form(...),
    design_idea: str = Form(...),
    grade_level: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    interests: Optional[str] = Form(None),
    include_exercises: bool = Form(True),
    include_prerequisites: bool = Form(True),
    ai_model: Optional[str] = Form(None),
    language: Optional[str] = Form(None),  # Language preference from frontend
    zhipu_text_model: Optional[str] = Form(None),  # Kept for backward compatibility
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Upload concept data and generate an interactive learning website using AI.
    Processing happens in the background, so the endpoint returns immediately.
    This is an alternative to PDF upload that works directly with text-based concept descriptions.
    """
    start_time = time.time()
    logger.info(f"🚀 Starting concept upload process for: {subject} - {concept_name}")

    try:
        # Prepare concept data
        concept_data = {
            "subject": subject,
            "concept_name": concept_name,
            "concept_overview": concept_overview,
            "mastery_points": mastery_points,
            "design_idea": design_idea
        }

        # Prepare user preferences
        user_preferences = {
            "grade_level": grade_level,
            "interests": interests.split(',') if interests else [],
            "description": description,
            "include_exercises": include_exercises,
            "include_prerequisites": include_prerequisites,
            "language": language or "zh"  # Use frontend language preference or default to Chinese
        }

        # Add AI model - prefer ai_model, fallback to zhipu_text_model for backward compatibility
        selected_model = ai_model or zhipu_text_model
        if selected_model:
            user_preferences["ai_model"] = selected_model
            # Also set zhipu_text_model for backward compatibility with ZhipuProvider
            if selected_model.startswith("glm-"):
                user_preferences["zhipu_text_model"] = selected_model

        # Create document record
        db_start = time.time()
        document = Document(
            title=concept_name,
            original_filename=f"concept_{concept_name}",
            file_path="",  # No file for concept input
            file_size=0,
            user_id=current_user.id,
            subject=subject,
            grade_level=grade_level,
            description=description,
            is_public=is_public,
            status="processing"
        )
        db.add(document)
        db.commit()
        db.refresh(document)
        db_time = time.time() - db_start
        logger.info(f"🗃️ Database record created in {db_time:.2f}s - Document ID: {document.id}")

        # Add background task to process the concept
        background_tasks.add_task(
            process_concept_background,
            document_id=document.id,
            concept_data=concept_data,
            user_prefs=user_preferences,
            db=db
        )

        total_time = time.time() - start_time
        logger.info(f"✅ Concept upload endpoint completed in {total_time:.2f}s - Processing continues in background")

        # Return immediately with document info
        result = {
            "id": document.id,
            "title": document.title,
            "original_filename": document.original_filename,
            "subject": document.subject,
            "grade_level": document.grade_level,
            "status": "processing",
            "message": "Concept uploaded successfully. Processing is happening in the background. Use the /documents/{id}/processing-status endpoint to check progress.",
            "created_at": document.created_at
        }

        return result

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Concept upload failed: {str(e)}")


@router.post("/concept/search-templates")
async def search_templates_for_concept(
    subject: str = Form(...),
    concept_name: str = Form(...),
    concept_overview: str = Form(...),
    grade_level: Optional[int] = Form(None),
    max_results: int = Form(5),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for templates matching a concept description.

    This endpoint allows users to see template options before committing to full generation.
    Returns a list of suitable templates that the user can then select.

    Form Fields:
        subject: Subject area (e.g., "Mathematics", "Science")
        concept_name: Name of the concept
        concept_overview: Brief description of the concept
        grade_level: Target grade level
        max_results: Maximum number of template results (default: 5)
    """
    try:
        # Build content info for template search
        content_info = {
            "title": concept_name,
            "description": concept_overview,
            "subject": subject,
            "grade_level": grade_level or 6,
            "category": subject.lower()
        }

        # Get AI processor and search templates
        ai_processor = get_ai_processor()

        result = await ai_processor.search_templates_for_user(
            content_info=content_info,
            workflow_type="website_concept",
            db_session_factory=lambda: db,
            max_results=max_results
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Template search failed: {str(e)}")


@router.post("/concept/generate-with-template")
async def generate_concept_with_template(
    background_tasks: BackgroundTasks,
    subject: str = Form(...),
    concept_name: str = Form(...),
    concept_overview: str = Form(...),
    mastery_points: str = Form(...),
    design_idea: str = Form(...),
    template_id: str = Form(...),  # Selected template ID
    grade_level: Optional[int] = Form(None),
    description: Optional[str] = Form(None),
    is_public: bool = Form(False),
    interests: Optional[str] = Form(None),
    customization_params: Optional[str] = Form(None),  # JSON string
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a website from concept using a selected template.

    Form Fields:
        subject: Subject area
        concept_name: Name of the concept
        concept_overview: Brief description
        mastery_points: Learning objectives
        design_idea: Design approach
        template_id: ID of the selected template
        grade_level: Target grade level
        description: Optional description
        is_public: Whether to make public
        interests: User interests (comma-separated)
        customization_params: Optional JSON string with template customization parameters
    """
    start_time = time.time()
    logger.info(f"🚀 Starting template-based concept generation for: {concept_name} with template: {template_id}")

    try:
        # Prepare concept data
        concept_data = {
            "subject": subject,
            "concept_name": concept_name,
            "concept_overview": concept_overview,
            "mastery_points": mastery_points,
            "design_idea": design_idea
        }

        # Prepare user preferences
        user_preferences = {
            "grade_level": grade_level,
            "interests": interests.split(',') if interests else [],
            "description": description,
            "subject": subject
        }

        # Parse customization params if provided
        custom_params = {}
        if customization_params:
            try:
                custom_params = json.loads(customization_params)
            except json.JSONDecodeError:
                logger.warning("Invalid customization_params JSON, using empty dict")

        # Create document record
        document = Document(
            title=concept_name,
            original_filename=f"concept_{concept_name}",
            file_path="",
            file_size=0,
            user_id=current_user.id,
            subject=subject,
            grade_level=grade_level,
            description=description,
            is_public=is_public,
            status="processing"
        )
        db.add(document)
        db.commit()
        db.refresh(document)

        # Add background task to process with template
        background_tasks.add_task(
            process_concept_with_template_background,
            document_id=document.id,
            concept_data=concept_data,
            user_prefs=user_preferences,
            template_id=template_id,
            customization_params=custom_params,
            db_session_factory=lambda: SessionLocal()
        )

        total_time = time.time() - start_time
        logger.info(f"✅ Template-based concept generation initiated in {total_time:.2f}s")

        return {
            "id": document.id,
            "title": document.title,
            "subject": document.subject,
            "grade_level": document.grade_level,
            "status": "processing",
            "message": f"Generating website using template: {template_id}",
            "template_id": template_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template-based concept generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


async def process_concept_with_template_background(
    document_id: int,
    concept_data: Dict,
    user_prefs: Dict,
    template_id: str,
    customization_params: Dict,
    db_session_factory
):
    """Background task to generate concept website using template."""
    logger.info(f"🔄 Starting template-based concept processing for document {document_id}")
    start_time = time.time()

    # Create a new database session for this background task
    from ..core.database import SessionLocal
    background_db = db_session_factory()

    try:
        # Get the document
        document = background_db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"❌ Document {document_id} not found")
            return

        # Get AI processor instance
        ai_processor = get_ai_processor()

        # Build content info for template generation
        content_info = {
            "title": concept_data.get("concept_name"),
            "description": concept_data.get("concept_overview"),
            "subject": concept_data.get("subject"),
            "grade_level": user_prefs.get("grade_level", 6),
            "mastery_points": concept_data.get("mastery_points"),
            "design_idea": concept_data.get("design_idea")
        }

        # Generate using selected template
        logger.info(f"🔄 Generating website with template {template_id}...")
        generation_start = time.time()

        result = await ai_processor.generate_with_selected_template(
            template_id=template_id,
            content_info=content_info,
            user_preferences=user_prefs,
            workflow_type="website_concept",
            db_session_factory=db_session_factory,
            customization_params=customization_params
        )

        generation_time = time.time() - generation_start
        logger.info(f"✅ Template generation completed in {generation_time:.2f}s")

        if result["status"] == "error":
            logger.error(f"❌ Template generation failed: {result.get('error')}")
            document.status = "error"
            document.error_message = result.get('error')
        else:
            # Update document with results
            document.status = "ready"
            document.page_count = 1
            document.pdf_metadata = {
                "template_used": template_id,
                "generation_method": "template_based"
            }
            document.processing_results = {
                "website": result["html"],
                "template_used": template_id,
                "generation_method": "template_based",
                "metadata": result.get("metadata", {})
            }
            logger.info(f"✅ Document {document_id} marked as ready")

        background_db.commit()

        total_time = time.time() - start_time
        logger.info(f"🎉 Template-based concept processing completed for document {document_id} in {total_time:.2f}s")

    except Exception as processing_error:
        logger.error(f"❌ Template-based concept processing error: {str(processing_error)}")
        try:
            document = background_db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.error_message = str(processing_error)
                background_db.commit()
        except Exception as db_error:
            logger.error(f"❌ Failed to update error status: {str(db_error)}")

    finally:
        background_db.close()


@router.post("/pdf/{document_id}/search-templates")
async def search_templates_for_pdf(
    document_id: int,
    max_results: int = 5,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for templates matching an uploaded PDF document.

    This endpoint analyzes the PDF and returns template options for website generation.
    """
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Build content info from document metadata
        content_info = {
            "title": document.title,
            "description": document.description or "",
            "subject": document.subject or "General",
            "grade_level": document.grade_level or 6,
            "category": (document.subject or "").lower()
        }

        # Get AI processor and search templates
        ai_processor = get_ai_processor()

        result = await ai_processor.search_templates_for_user(
            content_info=content_info,
            workflow_type="website_pdf",
            db_session_factory=lambda: db,
            max_results=max_results
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF template search failed: {e}")
        raise HTTPException(status_code=500, detail=f"Template search failed: {str(e)}")


@router.post("/pdf/{document_id}/generate-with-template")
async def generate_pdf_website_with_template(
    document_id: int,
    background_tasks: BackgroundTasks,
    template_id: str = Form(...),
    customization_params: Optional[str] = Form(None),  # JSON string
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a website from an uploaded PDF using a selected template.

    This endpoint regenerates the website for an existing PDF document using the specified template.
    """
    try:
        # Get document
        document = db.query(Document).filter(
            Document.id == document_id,
            Document.user_id == current_user.id
        ).first()

        if not document:
            raise HTTPException(status_code=404, detail="Document not found")

        # Parse customization params if provided
        custom_params = {}
        if customization_params:
            try:
                custom_params = json.loads(customization_params)
            except json.JSONDecodeError:
                logger.warning("Invalid customization_params JSON, using empty dict")

        # Build user preferences
        user_preferences = {
            "grade_level": document.grade_level,
            "subject": document.subject,
            "description": document.description
        }

        # Update document status
        document.status = "processing"
        db.commit()
        db.refresh(document)

        # Add background task to process with template
        background_tasks.add_task(
            process_pdf_with_template_background,
            document_id=document_id,
            file_path=document.file_path,
            user_prefs=user_preferences,
            template_id=template_id,
            customization_params=custom_params,
            db_session_factory=lambda: SessionLocal()
        )

        return {
            "id": document.id,
            "status": "processing",
            "message": f"Regenerating website using template: {template_id}",
            "template_id": template_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"PDF template generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Generation failed: {str(e)}")


async def process_pdf_with_template_background(
    document_id: int,
    file_path: str,
    user_prefs: Dict,
    template_id: str,
    customization_params: Dict,
    db_session_factory
):
    """Background task to generate PDF website using template."""
    logger.info(f"🔄 Starting template-based PDF processing for document {document_id}")
    start_time = time.time()

    # Create a new database session for this background task
    from ..core.database import SessionLocal
    background_db = db_session_factory()

    try:
        # Get the document
        document = background_db.query(Document).filter(Document.id == document_id).first()
        if not document:
            logger.error(f"❌ Document {document_id} not found")
            return

        # Get AI processor instance
        ai_processor = get_ai_processor()

        # Build content info for template generation
        content_info = {
            "title": document.title,
            "description": document.description or "",
            "subject": document.subject or "General",
            "grade_level": user_prefs.get("grade_level", 6)
        }

        # For PDF workflow, we need to extract images first
        # Get processed images from PDF
        logger.info(f"🔄 Extracting images from PDF...")
        processed_images = await ai_processor._convert_pdf_to_images(file_path)

        # Add images to content_info
        content_info["images"] = processed_images
        content_info["pdf_path"] = file_path

        # Generate using selected template
        logger.info(f"🔄 Generating website with template {template_id}...")
        generation_start = time.time()

        result = await ai_processor.generate_with_selected_template(
            template_id=template_id,
            content_info=content_info,
            user_preferences=user_prefs,
            workflow_type="website_pdf",
            db_session_factory=db_session_factory,
            customization_params=customization_params
        )

        generation_time = time.time() - generation_start
        logger.info(f"✅ Template generation completed in {generation_time:.2f}s")

        if result["status"] == "error":
            logger.error(f"❌ Template generation failed: {result.get('error')}")
            document.status = "error"
            document.error_message = result.get('error')
        else:
            # Update document with results
            document.status = "ready"
            document.page_count = len(processed_images)
            document.pdf_metadata = {
                "template_used": template_id,
                "generation_method": "template_based",
                "page_count": len(processed_images)
            }
            document.processing_results = {
                "website": result["html"],
                "template_used": template_id,
                "generation_method": "template_based",
                "metadata": result.get("metadata", {})
            }
            logger.info(f"✅ Document {document_id} marked as ready")

        background_db.commit()

        total_time = time.time() - start_time
        logger.info(f"🎉 Template-based PDF processing completed for document {document_id} in {total_time:.2f}s")

    except Exception as processing_error:
        logger.error(f"❌ Template-based PDF processing error: {str(processing_error)}")
        try:
            document = background_db.query(Document).filter(Document.id == document_id).first()
            if document:
                document.status = "error"
                document.error_message = str(processing_error)
                background_db.commit()
        except Exception as db_error:
            logger.error(f"❌ Failed to update error status: {str(db_error)}")

    finally:
        background_db.close()
