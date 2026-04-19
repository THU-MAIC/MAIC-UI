# Parallel Processing Pipeline Design

## Overview

The Parallel Processing Pipeline re-architects the PPT/PDF processing system to process multiple slides simultaneously instead of sequentially. This dramatically reduces processing time for large presentations (50+ slides) from 8-15 minutes down to 1-2 minutes.

## Problem Statement

**Current Issues:**
- Sequential processing: Each slide waits for the previous one to complete
- Single-threaded AI calls: Only one slide is analyzed at a time
- Slow for large presentations: 50 slides × 10 seconds = 500+ seconds (~8.5 minutes)
- Teachers wait too long for materials to be ready for class
- No progress feedback during long-running jobs
- Single point of failure: One failed slide can block the entire process

**Target Improvements:**
- 10-15x faster processing for large presentations
- Real-time progress updates via WebSocket
- Resilient to individual slide failures
- Scalable processing with configurable concurrency
- Better resource utilization (multi-core CPUs)

## Architecture

### Processing Flow Comparison

#### Current Sequential Flow
```
┌─────────────────────────────────────────────────────────────┐
│  Sequential Processing (Current)                             │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Batch 1 (slides 1-5)                                        │
│    ├─ Analyze → 10 seconds                                   │
│    ├─ Generate Demo → 15 seconds                             │
│    └─ Save → 1 second                                        │
│         Total: 26 seconds                                    │
│                                                               │
│  Batch 2 (slides 6-10)  [waits for batch 1]                  │
│    ├─ Analyze → 10 seconds                                   │
│    ├─ Generate Demo → 15 seconds                             │
│    └─ Save → 1 second                                        │
│         Total: 26 seconds                                    │
│                                                               │
│  ... repeat for 10 batches ...                               │
│                                                               │
│  Total Time: 26 seconds × 10 = 260 seconds (4.3 minutes)    │
│  for 50 slides                                               │
└─────────────────────────────────────────────────────────────┘
```

#### Proposed Parallel Flow
```
┌─────────────────────────────────────────────────────────────┐
│  Parallel Processing (Proposed)                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Stage 1: Parallel Analysis (all batches simultaneously)     │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Batch 1  │  │ Batch 2  │  │ Batch 3  │  ...              │
│  │ Analyze  │  │ Analyze  │  │ Analyze  │                   │
│  │ 10 sec   │  │ 10 sec   │  │ 10 sec   │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
│       ↓              ↓              ↓                         │
│  All complete in ~10 seconds (max of all batches)           │
│                                                               │
│  Stage 2: Parallel Demo Generation (all demos at once)      │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                  │
│  │ Demo 1   │  │ Demo 2   │  │ Demo 3   │  ...              │
│  │ Generate │  │ Generate │  │ Generate │                   │
│  │ 15 sec   │  │ 15 sec   │  │ 15 sec   │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
│       ↓              ↓              ↓                         │
│  All complete in ~15 seconds (max of all demos)             │
│                                                               │
│  Stage 3: Save all results                                   │
│  └─ 1-2 seconds                                              │
│                                                               │
│  Total Time: 10 + 15 + 2 = 27 seconds (vs 260 seconds)      │
│  Speedup: ~10x faster!                                       │
└─────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
backend/src/services/parallel_processing/
├── __init__.py
├── processor.py                   # Main parallel processor
├── orchestrator.py                # Pipeline orchestration
├── workers/
│   ├── __init__.py
│   ├── analysis_worker.py        # Slide analysis worker
│   └── generation_worker.py      # Demo generation worker
├── progress_tracker.py            # Real-time progress tracking
├── error_handler.py               # Error handling & retry logic
└── queue_manager.py               # Job queue management
```

## Core Components

### 1. Parallel Processor

```python
# backend/src/services/parallel_processing/processor.py

import asyncio
import time
import logging
from typing import List, Dict, Any, Callable, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class ProcessingStage(Enum):
    """Processing pipeline stages."""
    ANALYSIS = "analysis"
    DEMO_GENERATION = "demo_generation"
    FINALIZATION = "finalization"
    COMPLETE = "complete"


@dataclass
class ProcessingConfig:
    """Configuration for parallel processing."""
    # Concurrency limits
    max_concurrent_analyses: int = 5  # Max simultaneous AI analysis calls
    max_concurrent_generations: int = 10  # Max simultaneous demo generations

    # Retry settings
    max_retries: int = 3
    retry_delay: float = 1.0  # Initial delay in seconds
    retry_backoff_multiplier: float = 2.0

    # Progress settings
    progress_update_interval: float = 0.5  # Seconds between progress updates

    # Resource limits
    max_workers: int = 20  # Max total worker threads
    timeout_per_slide: int = 120  # Max seconds per slide before timeout


class ParallelProcessor:
    """
    Orchestrates parallel processing of slides/demos with controlled concurrency.

    Features:
    - Two-stage pipeline (analysis → generation)
    - Configurable concurrency limits
    - Automatic retry with exponential backoff
    - Progress tracking and reporting
    - Graceful error handling
    """

    def __init__(self, config: ProcessingConfig = None):
        """
        Initialize parallel processor.

        Args:
            config: Processing configuration (uses defaults if not provided)
        """
        self.config = config or ProcessingConfig()
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_workers)
        self._progress_callbacks = []

    def on_progress(self, callback: Callable[[Dict], None]):
        """Register a callback for progress updates."""
        self._progress_callbacks.append(callback)

    def _emit_progress(self, progress_data: Dict):
        """Emit progress to all registered callbacks."""
        for callback in self._progress_callbacks:
            try:
                callback(progress_data)
            except Exception as e:
                logger.error(f"Progress callback error: {e}")

    async def process_slides_parallel(
        self,
        slide_paths: List[str],
        analyze_fn: Callable,
        generate_fn: Callable,
        processing_config: Dict,
        user_prefs: Dict,
        document_id: int
    ) -> Tuple[List[Dict], Dict]:
        """
        Process all slides in parallel with two-stage pipeline.

        Args:
            slide_paths: List of slide image paths
            analyze_fn: Async function to analyze slides (signature: batch_images, prefs, config)
            generate_fn: Async function to generate demo HTML
            processing_config: Processing configuration from document
            user_prefs: User preferences dict
            document_id: Document ID for progress tracking

        Returns:
            Tuple of (processed_slides, statistics)
        """
        start_time = time.time()
        total_slides = len(slide_paths)

        logger.info(f"🚀 Starting parallel processing of {total_slides} slides")
        self._emit_progress({
            "stage": ProcessingStage.ANALYSIS,
            "progress": 0,
            "total": total_slides,
            "message": "Starting analysis..."
        })

        try:
            # Stage 1: Parallel Analysis
            analysis_start = time.time()
            analyses = await self._parallel_analyze(
                slide_paths=slide_paths,
                analyze_fn=analyze_fn,
                processing_config=processing_config,
                user_prefs=user_prefs,
                document_id=document_id
            )
            analysis_time = time.time() - analysis_start

            logger.info(f"✅ Stage 1 (Analysis) completed in {analysis_time:.2f}s")

            # Stage 2: Parallel Demo Generation
            generation_start = time.time()
            final_slides = await self._parallel_generate_demos(
                slide_paths=slide_paths,
                analyses=analyses,
                generate_fn=generate_fn,
                user_prefs=user_prefs,
                document_id=document_id
            )
            generation_time = time.time() - generation_start

            logger.info(f"✅ Stage 2 (Generation) completed in {generation_time:.2f}s")

            # Stage 3: Finalization
            self._emit_progress({
                "stage": ProcessingStage.FINALIZATION,
                "progress": total_slides,
                "total": total_slides,
                "message": "Finalizing..."
            })

            total_time = time.time() - start_time
            stats = {
                "total_slides": total_slides,
                "total_time": total_time,
                "analysis_time": analysis_time,
                "generation_time": generation_time,
                "avg_time_per_slide": total_time / total_slides,
                "slides_with_demos": sum(1 for s in final_slides if s.get('needs_demo'))
            }

            logger.info(f"✅ Parallel processing completed in {total_time:.2f}s")
            logger.info(f"   Average: {stats['avg_time_per_slide']:.2f}s per slide")

            self._emit_progress({
                "stage": ProcessingStage.COMPLETE,
                "progress": total_slides,
                "total": total_slides,
                "message": "Complete!",
                "statistics": stats
            })

            return final_slides, stats

        except Exception as e:
            logger.error(f"❌ Parallel processing failed: {e}", exc_info=True)
            raise

    async def _parallel_analyze(
        self,
        slide_paths: List[str],
        analyze_fn: Callable,
        processing_config: Dict,
        user_prefs: Dict,
        document_id: int
    ) -> Dict[int, Dict]:
        """
        Analyze slides in parallel batches.

        Args:
            slide_paths: List of slide image paths
            analyze_fn: Analysis function
            processing_config: Processing configuration
            user_prefs: User preferences
            document_id: Document ID

        Returns:
            Dict mapping slide_number → analysis_result
        """
        # Determine which slides to analyze
        slides_to_analyze = list(range(1, len(slide_paths) + 1))

        if processing_config.get("mode") == "specific_pages":
            slides_to_analyze = processing_config.get("selected_pages", slides_to_analyze)

        # Create batches
        batch_size = processing_config.get("batch_size", 5)
        batches = [
            slides_to_analyze[i:i + batch_size]
            for i in range(0, len(slides_to_analyze), batch_size)
        ]

        logger.info(f"📊 Processing {len(batches)} batches with max {self.config.max_concurrent_analyses} concurrent")
        logger.info(f"   Batch size: {batch_size}, Slides per batch: {[len(b) for b in batches[:3]]}...")

        # Semaphore to limit concurrent AI calls
        semaphore = asyncio.Semaphore(self.config.max_concurrent_analyses)

        async def process_batch_with_retry(batch: List[int], attempt: int = 1) -> Tuple[int, Dict]:
            """Process a single batch with retry logic."""
            async with semaphore:
                batch_images = [slide_paths[i - 1] for i in batch]

                try:
                    # Timeout protection
                    result = await asyncio.wait_for(
                        analyze_fn(batch_images, user_prefs, processing_config),
                        timeout=self.config.timeout_per_slide
                    )

                    # Map results back to slide numbers
                    slides_map = {}
                    response_slides = result.get('slides', [])

                    for idx, slide_info in enumerate(response_slides):
                        slide_num = batch[idx]
                        slide_info['slide_number'] = slide_num
                        slides_map[slide_num] = slide_info

                    # Update progress
                    self._emit_progress({
                        "stage": ProcessingStage.ANALYSIS,
                        "progress": len(slides_map),
                        "total": len(slide_paths),
                        "message": f"Analyzed batch with {len(batch)} slides"
                    })

                    return len(batch), slides_map

                except asyncio.TimeoutError:
                    logger.warning(f"⏱️ Batch {batch} timed out (attempt {attempt})")
                    if attempt < self.config.max_retries:
                        delay = self.config.retry_delay * (self.config.retry_backoff_multiplier ** (attempt - 1))
                        await asyncio.sleep(delay)
                        return await process_batch_with_retry(batch, attempt + 1)
                    else:
                        raise
                except Exception as e:
                    logger.error(f"❌ Batch {batch} failed (attempt {attempt}): {e}")
                    if attempt < self.config.max_retries:
                        delay = self.config.retry_delay * (self.config.retry_backoff_multiplier ** (attempt - 1))
                        await asyncio.sleep(delay)
                        return await process_batch_with_retry(batch, attempt + 1)
                    else:
                        # Return fallback analysis
                        logger.error(f"❌ Batch {batch} failed after {attempt} attempts, using fallback")
                        return len(batch), {
                            slide_num: {
                                'slide_number': slide_num,
                                'title': f'Slide {slide_num}',
                                'description': '',
                                'needs_demo': False,
                                'reason': 'Analysis failed after retries'
                            }
                            for slide_num in batch
                        }

        # Process all batches concurrently
        tasks = [process_batch_with_retry(batch) for batch in batches]

        # Gather results with progress tracking
        completed_count = 0
        all_analyses = {}

        for coro in asyncio.as_completed(tasks):
            batch_size, batch_results = await coro
            all_analyses.update(batch_results)
            completed_count += batch_size

            logger.info(f"   Progress: {completed_count}/{len(slide_paths)} slides analyzed")

        return all_analyses

    async def _parallel_generate_demos(
        self,
        slide_paths: List[str],
        analyses: Dict[int, Dict],
        generate_fn: Callable,
        user_prefs: Dict,
        document_id: int
    ) -> List[Dict]:
        """
        Generate demos in parallel for slides that need them.

        Args:
            slide_paths: List of slide image paths
            analyses: Analysis results from stage 1
            generate_fn: Demo generation function
            user_prefs: User preferences
            document_id: Document ID

        Returns:
            List of all slides with demos attached
        """
        # Filter slides that need demos
        demo_slides = [
            (slide_num, slide_paths[slide_num - 1], analyses[slide_num])
            for slide_num in range(1, len(slide_paths) + 1)
            if analyses.get(slide_num, {}).get('needs_demo', False)
        ]

        if not demo_slides:
            logger.info("ℹ️ No slides need demos, skipping generation")
            return self._build_final_slides(slide_paths, analyses, {})

        logger.info(f"🎨 Generating {len(demo_slides)} demos with max {self.config.max_concurrent_generations} concurrent")

        # Semaphore for demo generation
        semaphore = asyncio.Semaphore(self.config.max_concurrent_generations)

        async def generate_demo_with_retry(slide_num: int, image_path: str, slide_info: Dict, attempt: int = 1) -> Tuple[int, Optional[str], Optional[str]]:
            """Generate demo for a single slide with retry logic."""
            async with semaphore:
                try:
                    # Timeout protection
                    demo_html = await asyncio.wait_for(
                        generate_fn(image_path, slide_info, user_prefs),
                        timeout=self.config.timeout_per_slide
                    )

                    # Update progress
                    self._emit_progress({
                        "stage": ProcessingStage.DEMO_GENERATION,
                        "progress": slide_num,
                        "total": len(slide_paths),
                        "message": f"Generated demo for slide {slide_num}"
                    })

                    return slide_num, demo_html, None

                except asyncio.TimeoutError:
                    logger.warning(f"⏱️ Demo generation for slide {slide_num} timed out (attempt {attempt})")
                    if attempt < self.config.max_retries:
                        delay = self.config.retry_delay * (self.config.retry_backoff_multiplier ** (attempt - 1))
                        await asyncio.sleep(delay)
                        return await generate_demo_with_retry(slide_num, image_path, slide_info, attempt + 1)
                    else:
                        return slide_num, None, "Generation timed out"
                except Exception as e:
                    logger.error(f"❌ Demo generation for slide {slide_num} failed (attempt {attempt}): {e}")
                    if attempt < self.config.max_retries:
                        delay = self.config.retry_delay * (self.config.retry_backoff_multiplier ** (attempt - 1))
                        await asyncio.sleep(delay)
                        return await generate_demo_with_retry(slide_num, image_path, slide_info, attempt + 1)
                    else:
                        return slide_num, None, str(e)

        # Generate all demos concurrently
        tasks = [
            generate_demo_with_retry(num, path, info)
            for num, path, info in demo_slides
        ]

        demo_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Build demo map
        demo_map = {}
        success_count = 0
        failure_count = 0

        for result in demo_results:
            if isinstance(result, Exception):
                logger.error(f"❌ Unexpected error: {result}")
                failure_count += 1
                continue

            slide_num, demo_html, error = result
            if demo_html:
                demo_map[slide_num] = {
                    'demo_html': demo_html,
                    'demo_error': None
                }
                success_count += 1
            else:
                demo_map[slide_num] = {
                    'demo_html': None,
                    'demo_error': error
                }
                failure_count += 1

        logger.info(f"✅ Demo generation complete: {success_count} success, {failure_count} failed")

        return self._build_final_slides(slide_paths, analyses, demo_map)

    def _build_final_slides(
        self,
        slide_paths: List[str],
        analyses: Dict[int, Dict],
        demo_map: Dict[int, Dict]
    ) -> List[Dict]:
        """Build final slides data combining analyses and demos."""
        return [
            {
                'slide_number': i,
                'image_path': slide_paths[i - 1],
                'title': analyses.get(i, {}).get('title', f'Slide {i}'),
                'description': analyses.get(i, {}).get('description', ''),
                'needs_demo': analyses.get(i, {}).get('needs_demo', False),
                'demo_html': demo_map.get(i, {}).get('demo_html'),
                'demo_reason': analyses.get(i, {}).get('reason', ''),
                'demo_type': analyses.get(i, {}).get('demo_type', 'visualization'),
                'demo_error': demo_map.get(i, {}).get('demo_error')
            }
            for i in range(1, len(slide_paths) + 1)
        ]

    def shutdown(self):
        """Clean up resources."""
        logger.info("Shutting down parallel processor...")
        self.executor.shutdown(wait=True)
```

### 2. Progress Tracker with WebSocket

```python
# backend/src/services/parallel_processing/progress_tracker.py

import asyncio
import logging
from typing import Dict, Set
from dataclasses import dataclass, field
from datetime import datetime
from fastapi import WebSocket

logger = logging.getLogger(__name__)


@dataclass
class ProgressUpdate:
    """Progress update data."""
    document_id: int
    stage: str
    progress: int
    total: int
    message: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    statistics: Dict = None


class ProgressTracker:
    """
    Tracks processing progress and broadcasts to WebSocket clients.

    Features:
    - Multi-client support (multiple users can monitor same job)
    - Automatic cleanup of disconnected clients
    - Progress history for reconnecting clients
    """

    def __init__(self):
        # document_id -> Set of WebSocket connections
        self._connections: Dict[int, Set[WebSocket]] = {}

        # document_id -> Progress history
        self._history: Dict[int, list] = {}

    async def subscribe(self, document_id: int, websocket: WebSocket):
        """Subscribe a client to progress updates for a document."""
        if document_id not in self._connections:
            self._connections[document_id] = set()

        self._connections[document_id].add(websocket)
        logger.info(f"Client subscribed to document {document_id} (total: {len(self._connections[document_id])})")

        # Send historical progress
        if document_id in self._history:
            for update in self._history[document_id]:
                await self._send_to_client(websocket, update)

    async def unsubscribe(self, document_id: int, websocket: WebSocket):
        """Unsubscribe a client from progress updates."""
        if document_id in self._connections:
            self._connections[document_id].discard(websocket)
            logger.info(f"Client unsubscribed from document {document_id}")

    async def broadcast(self, update: ProgressUpdate):
        """Broadcast progress update to all subscribers."""
        document_id = update.document_id

        # Store in history
        if document_id not in self._history:
            self._history[document_id] = []
        self._history[document_id].append(update)

        # Keep only last 100 updates
        if len(self._history[document_id]) > 100:
            self._history[document_id] = self._history[document_id][-100:]

        # Broadcast to all connected clients
        if document_id in self._connections:
            # Create a copy of the set to avoid modification during iteration
            clients = self._connections[document_id].copy()

            for client in clients:
                try:
                    await self._send_to_client(client, update)
                except Exception as e:
                    logger.warning(f"Failed to send update to client: {e}")
                    # Remove disconnected client
                    self._connections[document_id].discard(client)

    async def _send_to_client(self, websocket: WebSocket, update: ProgressUpdate):
        """Send update to a specific client."""
        try:
            await websocket.send_json({
                "stage": update.stage,
                "progress": update.progress,
                "total": update.total,
                "percentage": int((update.progress / update.total) * 100) if update.total > 0 else 0,
                "message": update.message,
                "timestamp": update.timestamp.isoformat(),
                "statistics": update.statistics
            })
        except Exception as e:
            logger.error(f"Error sending to client: {e}")
            raise

    def cleanup(self, document_id: int):
        """Clean up resources for a completed document."""
        if document_id in self._connections:
            del self._connections[document_id]
        if document_id in self._history:
            del self._history[document_id]


# Global singleton
_tracker: ProgressTracker = None


def get_progress_tracker() -> ProgressTracker:
    """Get or create the global progress tracker singleton."""
    global _tracker
    if _tracker is None:
        _tracker = ProgressTracker()
    return _tracker
```

### 3. WebSocket Endpoint

```python
# backend/src/api/websocket.py

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from ..services.parallel_processing.progress_tracker import get_progress_tracker, ProgressUpdate
from ..core.database import get_db
from ..models.user import User
from ..core.security import get_current_user

router = APIRouter()


@router.websocket("/ws/documents/{document_id}/progress")
async def document_progress_websocket(
    document_id: int,
    websocket: WebSocket,
    db: Session = Depends(get_db)
):
    """
    WebSocket endpoint for real-time processing progress updates.

    Client connects to: ws://localhost:8000/api/ws/documents/{document_id}/progress

    Message format:
    {
        "stage": "analysis" | "demo_generation" | "finalization" | "complete",
        "progress": 5,
        "total": 50,
        "percentage": 10,
        "message": "Analyzing slides...",
        "timestamp": "2025-01-16T10:30:00",
        "statistics": {
            "total_slides": 50,
            "total_time": 45.2,
            "avg_time_per_slide": 0.9
        }
    }
    """
    tracker = get_progress_tracker()

    await websocket.accept()
    logger.info(f"WebSocket connected for document {document_id}")

    # Subscribe to progress updates
    await tracker.subscribe(document_id, websocket)

    try:
        # Keep connection alive and handle client messages
        while True:
            data = await websocket.receive_text()

            # Handle ping/pong to keep connection alive
            if data == "ping":
                await websocket.send_text("pong")

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected for document {document_id}")
        await tracker.unsubscribe(document_id, websocket)
    except Exception as e:
        logger.error(f"WebSocket error for document {document_id}: {e}")
        await tracker.unsubscribe(document_id, websocket)
```

### 4. Integration with PPT Processor

```python
# backend/src/services/ppt_processor.py (modifications)

import asyncio
import time
import logging
from ..services.parallel_processing.processor import ParallelProcessor, ProcessingConfig
from ..services.parallel_processing.progress_tracker import get_progress_tracker, ProgressUpdate

logger = logging.getLogger(__name__)


async def process_ppt_background(
    document_id: int,
    file_path: str,
    file_type: str,
    user_prefs: Dict,
    db_session_factory
):
    """
    Background task to process PPT/PPTX/PDF asynchronously with parallel processing.

    NEW: Uses parallel processing for 10-15x speedup.
    """
    logger.info(f"🚀 Starting PARALLEL PPT processing for document {document_id}")
    start_time = time.time()

    # Create new database session
    db = db_session_factory()

    # Get progress tracker
    tracker = get_progress_tracker()

    try:
        from ..models.ppt_document import PPTDocument

        # Get document
        document = db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
        if not document:
            logger.error(f"Document {document_id} not found")
            return

        # Get processing config from document
        processing_config = document.processing_config or {}

        # Initialize processor with AI provider
        from .ai_processor import get_ai_processor
        ai_processor = get_ai_processor()
        processor = PPTProcessor(ai_provider=ai_processor)

        # Convert file to slide images
        logger.info(f"📄 Converting {file_type} to slides...")
        slide_paths, pdf_used = processor.process_file(file_path, file_type, document_id)
        logger.info(f"✅ Converted {len(slide_paths)} slides")

        # Initialize parallel processor with configuration
        parallel_config = ProcessingConfig(
            max_concurrent_analyses=5,
            max_concurrent_generations=10,
            max_retries=3,
            timeout_per_slide=120
        )

        parallel_proc = ParallelProcessor(config=parallel_config)

        # Register progress callback to broadcast via WebSocket
        async def progress_callback(progress_data):
            update = ProgressUpdate(
                document_id=document_id,
                stage=progress_data.get("stage", "unknown"),
                progress=progress_data.get("progress", 0),
                total=progress_data.get("total", 0),
                message=progress_data.get("message", ""),
                statistics=progress_data.get("statistics")
            )
            await tracker.broadcast(update)

        parallel_proc.on_progress(progress_callback)

        # Process slides in parallel
        logger.info(f"🔄 Processing {len(slide_paths)} slides in parallel...")
        final_slides, stats = await parallel_proc.process_slides_parallel(
            slide_paths=slide_paths,
            analyze_fn=processor.demo_analyzer.analyze_slides_for_demo_opportunities,
            generate_fn=processor.demo_analyzer.generate_demo_html,
            processing_config=processing_config,
            user_prefs=user_prefs,
            document_id=document_id
        )

        # Update document with results
        document.slides_data = {"slides": final_slides}
        document.analysis_results = {"statistics": stats}
        document.status = "ready"
        document.processing_config = {
            **processing_config,
            "parallel_processing": True,
            "processing_stats": stats
        }

        db.commit()
        db.refresh(document)

        total_time = time.time() - start_time
        logger.info(f"✅ PPT processing completed for document {document_id} in {total_time:.2f}s")
        logger.info(f"   Statistics: {stats}")

        # Send final progress update
        await tracker.broadcast(ProgressUpdate(
            document_id=document_id,
            stage="complete",
            progress=len(slide_paths),
            total=len(slide_paths),
            message=f"Complete! Processed {len(slide_paths)} slides in {total_time:.1f}s",
            statistics=stats
        ))

        # Cleanup
        tracker.cleanup(document_id)

    except Exception as e:
        logger.error(f"❌ Error processing PPT document {document_id}: {e}", exc_info=True)

        # Update document with error
        try:
            document = db.query(PPTDocument).filter(PPTDocument.id == document_id).first()
            if document:
                document.status = "error"
                document.error_message = str(e)
                db.commit()

            # Broadcast error
            await tracker.broadcast(ProgressUpdate(
                document_id=document_id,
                stage="error",
                progress=0,
                total=0,
                message=f"Error: {str(e)}"
            ))
        except Exception as db_error:
            logger.error(f"Failed to update error status: {db_error}")

    finally:
        db.close()
```

## Frontend Integration

### Progress Monitor Component

```typescript
// frontend/src/components/processing/ProgressMonitor.tsx

import React, { useEffect, useState, useRef } from 'react';

interface ProgressMessage {
  stage: string;
  progress: number;
  total: number;
  percentage: number;
  message: string;
  timestamp: string;
  statistics?: {
    total_slides: number;
    total_time: number;
    avg_time_per_slide: number;
  };
}

interface ProcessingStage {
  key: string;
  label: string;
  icon: string;
}

const STAGES: ProcessingStage[] = [
  { key: 'analysis', label: 'Analyzing Slides', icon: '🔍' },
  { key: 'demo_generation', label: 'Generating Demos', icon: '🎨' },
  { key: 'finalization', label: 'Finalizing', icon: '✅' },
  { key: 'complete', label: 'Complete!', icon: '🎉' }
];

export const ProgressMonitor: React.FC<{ documentId: number }> = ({ documentId }) => {
  const [progress, setProgress] = useState<ProgressMessage | null>(null);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connectWebSocket = () => {
      const ws = new WebSocket(`ws://localhost:8000/api/ws/documents/${documentId}/progress`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setConnected(true);
        setError(null);

        // Send periodic ping to keep connection alive
        const pingInterval = setInterval(() => {
          if (ws.readyState === WebSocket.OPEN) {
            ws.send('ping');
          }
        }, 30000);

        wsRef.current = ws;

        return () => {
          clearInterval(pingInterval);
        };
      };

      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        setProgress(data);
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
        setError('Connection error');
        setConnected(false);
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setConnected(false);

        // Attempt to reconnect after 3 seconds
        setTimeout(() => {
          if (documentId) {
            connectWebSocket();
          }
        }, 3000);
      };
    };

    connectWebSocket();

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [documentId]);

  if (!progress) {
    return (
      <div className="progress-monitor initializing">
        <div className="spinner"></div>
        <p>Connecting to processing service...</p>
      </div>
    );
  }

  const currentStageIndex = STAGES.findIndex(s => s.key === progress.stage);
  const isComplete = progress.stage === 'complete';

  return (
    <div className="progress-monitor">
      <div className="connection-status">
        <span className={`status-indicator ${connected ? 'connected' : 'disconnected'}`} />
        {connected ? 'Connected' : 'Reconnecting...'}
      </div>

      {/* Stage indicators */}
      <div className="stages">
        {STAGES.map((stage, index) => {
          const isCompleted = index < currentStageIndex;
          const isCurrent = index === currentStageIndex;
          const isPending = index > currentStageIndex;

          return (
            <div
              key={stage.key}
              className={`stage ${isCompleted ? 'completed' : ''} ${isCurrent ? 'current' : ''} ${isPending ? 'pending' : ''}`}
            >
              <span className="stage-icon">{stage.icon}</span>
              <span className="stage-label">{stage.label}</span>
            </div>
          );
        })}
      </div>

      {/* Progress bar */}
      <div className="progress-bar-container">
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${progress.percentage}%` }}
          />
        </div>
        <div className="progress-text">
          {progress.progress} / {progress.total} slides ({progress.percentage}%)
        </div>
      </div>

      {/* Status message */}
      <div className="status-message">
        {progress.message}
      </div>

      {/* Statistics (when complete) */}
      {isComplete && progress.statistics && (
        <div className="statistics">
          <h4>Processing Statistics</h4>
          <div className="stat-grid">
            <div className="stat-item">
              <div className="stat-value">{progress.statistics.total_slides}</div>
              <div className="stat-label">Total Slides</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{progress.statistics.total_time.toFixed(1)}s</div>
              <div className="stat-label">Total Time</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{progress.statistics.avg_time_per_slide.toFixed(2)}s</div>
              <div className="stat-label">Avg Per Slide</div>
            </div>
            <div className="stat-item">
              <div className="stat-value">{progress.statistics.slides_with_demos || 0}</div>
              <div className="stat-label">Demos Generated</div>
            </div>
          </div>
        </div>
      )}

      {error && (
        <div className="error-message">
          ⚠️ {error}
        </div>
      )}
    </div>
  );
};
```

## Performance Comparison

### Benchmark Results (Estimated)

| Presentation Size | Sequential | Parallel | Speedup |
|-------------------|-----------|----------|---------|
| 10 slides | 26 seconds | 18 seconds | 1.4x |
| 25 slides | 65 seconds | 22 seconds | 3x |
| 50 slides | 130 seconds | 27 seconds | **4.8x** |
| 100 slides | 260 seconds | 52 seconds | **5x** |
| 200 slides | 520 seconds | 104 seconds | **5x** |

**Note**: Speedup increases with presentation size due to better parallelization. Maximum theoretical speedup is limited by:
- Number of concurrent AI calls allowed (configurable)
- Batch size (larger batches = fewer parallel tasks)
- Network latency for API calls

## Configuration Tuning

### Recommended Settings by Use Case

```python
# Default (balanced)
config = ProcessingConfig(
    max_concurrent_analyses=5,
    max_concurrent_generations=10,
    max_retries=3
)

# High-throughput (powerful server, many API quota)
config = ProcessingConfig(
    max_concurrent_analyses=10,
    max_concurrent_generations=20,
    max_retries=3
)

# Conservative (limited resources)
config = ProcessingConfig(
    max_concurrent_analyses=2,
    max_concurrent_generations=5,
    max_retries=2
)

# Development/testing
config = ProcessingConfig(
    max_concurrent_analyses=1,
    max_concurrent_generations=2,
    max_retries=1
)
```

## Implementation Timeline

### Phase 1: Core Implementation (Week 1)
- [ ] Implement ParallelProcessor class
- [ ] Build progress tracking system
- [ ] Add error handling and retry logic
- [ ] Write unit tests

### Phase 2: Integration (Week 2)
- [ ] Integrate with PPT processor
- [ ] Add WebSocket progress endpoint
- [ ] Build frontend progress monitor
- [ ] End-to-end testing

### Phase 3: Optimization (Week 3)
- [ ] Performance benchmarking
- [ ] Configuration tuning
- [ ] Resource monitoring
- [ ] Load testing

## Success Metrics

- **Processing time**: 5-10x faster for 50+ slide presentations
- **Resource utilization**: 80%+ CPU usage during processing
- **Reliability**: <5% failure rate with automatic retry
- **User experience**: Real-time progress updates for all processing jobs
- **Scalability**: Handle 100+ concurrent processing jobs
