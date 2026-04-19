# Collaborative Editing & Versioning Design

## Overview

The Collaborative Editing & Versioning system enables multiple teachers to work together on the same presentation materials, with full version history tracking, comments, and permission management. This transforms the platform from a single-user tool into a collaborative workspace for curriculum development.

## Problem Statement

**Current Issues:**
- Single-user workflow: Teachers work in isolation
- No version history: Can't revert to previous versions
- No peer review: No way to comment on or suggest changes
- Reinventing the wheel: Multiple teachers create similar content separately
- Lost work: Accidental deletions or bad edits can't be undone
- No accountability: Can't see who made what changes

**Target Improvements:**
- Multi-user collaboration on the same documents
- Complete version history with one-click restore
- Comments and annotations for peer review
- Permission-based access control
- Activity tracking and change logs
- Curriculum sharing across departments/schools

## Architecture

### Data Model

```mermaid
erDiagram
    Document ||--o{ DocumentVersion : has
    Document ||--o{ DocumentComment : has
    Document ||--o{ CollaborationInvite : has
    Document ||--o{ CollaborationSession : has
    User ||--o{ DocumentVersion : creates
    User ||--o{ DocumentComment : writes
    User ||--o{ CollaborationInvite : sends
    User ||--o{ CollaborationInvite : receives
    User ||--o{ CollaborationSession : starts
    DocumentComment ||--o{ DocumentComment : replies to

    Document {
        int id PK
        int user_id FK
        string title
        string original_filename
        json slides_data
        json analysis_results
        json processing_config
        string status
        datetime created_at
        datetime updated_at
    }

    DocumentVersion {
        int id PK
        int document_id FK
        int version_number
        int created_by FK
        string change_summary
        string change_type
        json slides_snapshot
        json analysis_snapshot
        json processing_config_snapshot
        datetime created_at
    }

    DocumentComment {
        int id PK
        int document_id FK
        int slide_number
        int author_id FK
        int parent_comment_id FK
        text content
        string comment_type
        boolean is_resolved
        int resolved_by FK
        datetime resolved_at
        datetime created_at
        datetime updated_at
    }

    CollaborationInvite {
        int id PK
        int document_id FK
        int invited_by FK
        int invited_user_id FK
        string permission
        string status
        datetime created_at
        datetime accepted_at
    }

    CollaborationSession {
        int id PK
        int document_id FK
        int started_by FK
        json participants
        boolean is_active
        datetime started_at
        datetime ended_at
    }
```

## Database Schema

### 1. Document Versions

```python
# backend/src/models/document_version.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, JSON, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class DocumentVersion(Base):
    """
    Version history for documents.

    Tracks all changes to a document with full snapshots,
    enabling restoration to any previous state.
    """
    __tablename__ = "document_versions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    version_number = Column(Integer, nullable=False)

    # Version metadata
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    change_summary = Column(String(500))  # Human-readable summary
    change_type = Column(String(50))  # "initial", "ui_modification", "slide_update", "content_edit"

    # Full snapshots of document state at this version
    slides_snapshot = Column(JSON)  # Complete slides_data
    analysis_snapshot = Column(JSON)  # Complete analysis_results
    processing_config_snapshot = Column(JSON)  # Complete processing_config

    # Additional metadata
    processing_time = Column(Integer)  # Processing time in seconds
    slide_count = Column(Integer)  # Number of slides in this version
    generated_by = Column(String(50))  # "template", "ai", "manual"

    # Relationships
    creator = relationship("User", backref="created_versions", foreign_keys=[created_by])
    document = relationship("Document", backref="versions")

    __table_args__ = (
        Index('idx_document_version', 'document_id', 'version_number'),
        Index('idx_version_created', 'document_id', 'created_at'),
    )

    def to_dict(self):
        """Convert version to dictionary for API responses."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "version_number": self.version_number,
            "created_at": self.created_at.isoformat(),
            "created_by": self.creator.username if self.creator else "Unknown",
            "change_summary": self.change_summary,
            "change_type": self.change_type,
            "slide_count": self.slide_count,
            "processing_time": self.processing_time,
            "generated_by": self.generated_by
        }
```

### 2. Document Comments

```python
# backend/src/models/document_comment.py

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class DocumentComment(Base):
    """
    Comments on specific slides or overall document.

    Supports:
    - Threaded discussions (replies to comments)
    - Multiple comment types (suggestion, question, issue, praise)
    - Resolution tracking
    """
    __tablename__ = "document_comments"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    slide_number = Column(Integer, nullable=True)  # NULL = overall document comment

    # Author and threading
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    parent_comment_id = Column(Integer, ForeignKey("document_comments.id"), nullable=True)

    # Comment content
    content = Column(Text, nullable=False)
    comment_type = Column(String(50), default="suggestion")  # "suggestion", "question", "issue", "praise"

    # Status tracking
    is_resolved = Column(Boolean, default=False)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    resolved_at = Column(DateTime, nullable=True)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("User", foreign_keys=[author_id], backref="authored_comments")
    resolver = relationship("User", foreign_keys=[resolved_by])
    parent_comment = relationship("DocumentComment", remote_side=[id], backref="replies")
    document = relationship("Document", backref="comments")

    def to_dict(self, include_replies=False):
        """Convert comment to dictionary for API responses."""
        data = {
            "id": self.id,
            "document_id": self.document_id,
            "slide_number": self.slide_number,
            "content": self.content,
            "comment_type": self.comment_type,
            "author": self.author.username if self.author else "Unknown",
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "is_resolved": self.is_resolved,
            "resolved_by": self.resolver.username if self.resolver else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "reply_count": len(self.replies) if self.replies else 0
        }

        if include_replies and self.replies:
            data["replies"] = [reply.to_dict() for reply in self.replies]

        return data
```

### 3. Collaboration Invites

```python
# backend/src/models/collaboration_invite.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base
import enum

class InviteStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    DECLINED = "declined"
    REVOKED = "revoked"

class PermissionLevel(str, enum.Enum):
    VIEWER = "viewer"  # Can only view
    COMMENTER = "commenter"  # Can view and comment
    EDITOR = "editor"  # Can view, comment, and edit
    OWNER = "owner"  # Full control including delete

class CollaborationInvite(Base):
    """
    Invitations for users to collaborate on documents.

    Supports:
    - Permission-based access control
    - Invite status tracking
    - Expiration (optional, future enhancement)
    """
    __tablename__ = "collaboration_invites"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    invited_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    invited_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Permission and status
    permission = Column(String(50), default=PermissionLevel.EDITOR.value)
    status = Column(String(50), default=InviteStatus.PENDING.value)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    accepted_at = Column(DateTime, nullable=True)

    # Optional expiration (future)
    expires_at = Column(DateTime, nullable=True)

    # Relationships
    inviter = relationship("User", foreign_keys=[invited_by], backref="sent_invites")
    invited_user = relationship("User", foreign_keys=[invited_user_id], backref="received_invites")
    document = relationship("Document", backref="collaboration_invites")

    def to_dict(self):
        """Convert invite to dictionary for API responses."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "document_title": self.document.title if self.document else "Unknown",
            "invited_by": self.inviter.username if self.inviter else "Unknown",
            "invited_user": self.invited_user.username if self.invited_user else "Unknown",
            "permission": self.permission,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "accepted_at": self.accepted_at.isoformat() if self.accepted_at else None,
            "expires_at": self.expires_at.isoformat() if self.expires_at else None
        }
```

### 4. Collaboration Sessions

```python
# backend/src/models/collaboration_session.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class CollaborationSession(Base):
    """
    Active collaboration sessions for real-time editing.

    Tracks:
    - Who is currently editing/viewing a document
    - Session start/end times
    - All participants in the session
    """
    __tablename__ = "collaboration_sessions"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    started_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Session tracking
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    # Participants (list of user IDs)
    participants = Column(JSON, default=list)

    # Session metadata
    max_participants = Column(Integer, default=10)
    current_participant_count = Column(Integer, default=1)

    # Relationships
    starter = relationship("User", backref="started_sessions")
    document = relationship("Document", backref="collaboration_sessions")

    def to_dict(self):
        """Convert session to dictionary for API responses."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "started_by": self.starter.username if self.starter else "Unknown",
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat() if self.ended_at else None,
            "is_active": self.is_active,
            "participants": self.participants,
            "current_participant_count": self.current_participant_count
        }
```

### 5. Document Access (New Model for Permissions)

```python
# backend/src/models/document_access.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from ..core.database import Base

class DocumentAccess(Base):
    """
    Explicit access control for documents.

    Defines who can access what documents with what permissions.
    This is created when an invite is accepted.
    """
    __tablename__ = "document_access"

    id = Column(Integer, primary_key=True, index=True)
    document_id = Column(Integer, ForeignKey("documents.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Permission level
    permission = Column(String(50), nullable=False)

    # Granted by (who gave this permission)
    granted_by = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    granted_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", foreign_keys=[user_id], backref="document_access")
    granter = relationship("User", foreign_keys=[granted_by])
    document = relationship("Document", backref="access_list")

    __table_args__ = (
        UniqueConstraint('document_id', 'user_id', name='unique_document_user_access'),
    )

    def to_dict(self):
        """Convert access record to dictionary."""
        return {
            "id": self.id,
            "document_id": self.document_id,
            "user_id": self.user_id,
            "user_name": self.user.username if self.user else "Unknown",
            "permission": self.permission,
            "granted_by": self.granter.username if self.granter else "Unknown",
            "granted_at": self.granted_at.isoformat()
        }
```

## API Endpoints

### 1. Version Management

```python
# backend/src/api/versioning.py

from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List
from ..core.database import get_db
from ..models.document import Document
from ..models.document_version import DocumentVersion
from ..models.user import User
from ..core.security import get_current_user
from pydantic import BaseModel

router = APIRouter()


class CreateVersionRequest(BaseModel):
    change_summary: str
    change_type: str = "manual"  # "initial", "ui_modification", "slide_update", "content_edit"


@router.post("/documents/{document_id}/versions")
async def create_version(
    document_id: int,
    request: CreateVersionRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a manual version snapshot of a document.

    Use this to:
    - Save a milestone before major changes
    - Document important changes
    - Create restore points
    """
    document = db.query(Document).filter(
        Document.id == document_id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    # Check permission (owner or editor)
    # (Add permission check here)

    # Get current version number
    latest_version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).order_by(DocumentVersion.version_number.desc()).first()

    new_version_number = (latest_version.version_number + 1) if latest_version else 1

    # Create version snapshot
    version = DocumentVersion(
        document_id=document_id,
        version_number=new_version_number,
        created_by=current_user.id,
        change_summary=request.change_summary,
        change_type=request.change_type,
        slides_snapshot=document.slides_data,
        analysis_snapshot=document.analysis_results,
        processing_config_snapshot=document.processing_config,
        slide_count=len(document.slides_data.get("slides", [])) if document.slides_data else 0
    )

    db.add(version)
    db.commit()
    db.refresh(version)

    return {
        "version_number": new_version_number,
        "message": f"Version {new_version_number} created successfully",
        "version": version.to_dict()
    }


@router.get("/documents/{document_id}/versions")
async def list_versions(
    document_id: int,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all versions of a document.

    Returns:
        List of versions in reverse chronological order (newest first)
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")

    # Check permission
    # (Add permission check here)

    versions = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).order_by(DocumentVersion.version_number.desc()).offset(skip).limit(limit).all()

    return {
        "document_id": document_id,
        "total_versions": len(versions),
        "versions": [v.to_dict() for v in versions]
    }


@router.get("/documents/{document_id}/versions/{version_number}")
async def get_version(
    document_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed information about a specific version."""
    version = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id,
        DocumentVersion.version_number == version_number
    ).first()

    if not version:
        raise HTTPException(404, "Version not found")

    return {
        "version": version.to_dict(),
        "slides": version.slides_snapshot,
        "analysis": version.analysis_snapshot,
        "config": version.processing_config_snapshot
    }


@router.post("/documents/{document_id}/versions/{version_number}/restore")
async def restore_version(
    document_id: int,
    version_number: int,
    change_summary: str = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Restore document to a previous version.

    Process:
    1. Creates a version of current state (backup)
    2. Restores requested version
    3. Creates new version recording the restore

    Args:
        version_number: Version to restore
        change_summary: Optional reason for restoration
    """
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id  # Only owner can restore
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    version_to_restore = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id,
        DocumentVersion.version_number == version_number
    ).first()

    if not version_to_restore:
        raise HTTPException(404, "Version not found")

    # Step 1: Create backup of current state
    current_version_count = db.query(DocumentVersion).filter(
        DocumentVersion.document_id == document_id
    ).count()

    backup_version = DocumentVersion(
        document_id=document_id,
        version_number=current_version_count + 1,
        created_by=current_user.id,
        change_summary=f"Auto-backup before restoring to version {version_number}",
        change_type="restore_backup",
        slides_snapshot=document.slides_data,
        analysis_snapshot=document.analysis_results,
        processing_config_snapshot=document.processing_config,
        slide_count=len(document.slides_data.get("slides", [])) if document.slides_data else 0
    )
    db.add(backup_version)

    # Step 2: Restore the requested version
    document.slides_data = version_to_restore.slides_snapshot
    document.analysis_results = version_to_restore.analysis_snapshot
    document.processing_config = version_to_restore.processing_config_snapshot

    # Step 3: Create version recording the restore
    restore_version = DocumentVersion(
        document_id=document_id,
        version_number=current_version_count + 2,
        created_by=current_user.id,
        change_summary=change_summary or f"Restored to version {version_number}",
        change_type="restore",
        slides_snapshot=version_to_restore.slides_snapshot,
        analysis_snapshot=version_to_restore.analysis_snapshot,
        processing_config_snapshot=version_to_restore.processing_config_snapshot,
        slide_count=version_to_restore.slide_count
    )
    db.add(restore_version)

    db.commit()

    return {
        "message": f"Document restored to version {version_number}",
        "backup_version": current_version_count + 1,
        "current_version": current_version_count + 2
    }


@router.delete("/documents/{document_id}/versions/{version_number}")
async def delete_version(
    document_id: int,
    version_number: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a specific version.

    Note: Cannot delete the current version (most recent).
    """
    # Implementation
    pass
```

### 2. Comments API

```python
# backend/src/api/comments.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..models.document import Document
from ..models.document_comment import DocumentComment
from ..models.user import User
from ..core.security import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class CreateCommentRequest(BaseModel):
    content: str
    slide_number: Optional[int] = None
    comment_type: str = "suggestion"
    parent_comment_id: Optional[int] = None


class UpdateCommentRequest(BaseModel):
    content: str


@router.get("/documents/{document_id}/comments")
async def get_comments(
    document_id: int,
    slide_number: Optional[int] = None,
    include_resolved: bool = False,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get comments for a document or specific slide.

    Query params:
    - slide_number: Filter by slide (None = document-level comments)
    - include_resolved: Include resolved comments (default: false)
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")

    # Build query
    query = db.query(DocumentComment).filter(
        DocumentComment.document_id == document_id,
        DocumentComment.slide_number == slide_number,
        DocumentComment.parent_comment_id == None  # Top-level only
    )

    if not include_resolved:
        query = query.filter(DocumentComment.is_resolved == False)

    comments = query.order_by(DocumentComment.created_at.desc()).all()

    return {
        "document_id": document_id,
        "slide_number": slide_number,
        "total_comments": len(comments),
        "comments": [c.to_dict(include_replies=True) for c in comments]
    }


@router.post("/documents/{document_id}/comments")
async def create_comment(
    document_id: int,
    request: CreateCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Add a comment to a document or slide."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")

    # Validate slide number
    if request.slide_number is not None:
        total_slides = len(document.slides_data.get("slides", [])) if document.slides_data else 0
        if request.slide_number < 1 or request.slide_number > total_slides:
            raise HTTPException(400, f"Invalid slide number. Must be between 1 and {total_slides}")

    # Validate parent comment if this is a reply
    if request.parent_comment_id:
        parent = db.query(DocumentComment).filter(
            DocumentComment.id == request.parent_comment_id,
            DocumentComment.document_id == document_id
        ).first()
        if not parent:
            raise HTTPException(404, "Parent comment not found")

    comment = DocumentComment(
        document_id=document_id,
        slide_number=request.slide_number,
        author_id=current_user.id,
        parent_comment_id=request.parent_comment_id,
        content=request.content,
        comment_type=request.comment_type
    )

    db.add(comment)
    db.commit()
    db.refresh(comment)

    return {
        "message": "Comment created successfully",
        "comment": comment.to_dict()
    }


@router.put("/comments/{comment_id}")
async def update_comment(
    comment_id: int,
    request: UpdateCommentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update an existing comment (only by author)."""
    comment = db.query(DocumentComment).filter(DocumentComment.id == comment_id).first()

    if not comment:
        raise HTTPException(404, "Comment not found")

    # Check permission (only author can edit)
    if comment.author_id != current_user.id:
        raise HTTPException(403, "You can only edit your own comments")

    comment.content = request.content
    comment.updated_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Comment updated successfully",
        "comment": comment.to_dict()
    }


@router.put("/comments/{comment_id}/resolve")
async def resolve_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Mark a comment as resolved.

    Any user with edit permission can resolve comments.
    """
    comment = db.query(DocumentComment).filter(DocumentComment.id == comment_id).first()

    if not comment:
        raise HTTPException(404, "Comment not found")

    # Check permission
    # (Add permission check here)

    comment.is_resolved = True
    comment.resolved_by = current_user.id
    comment.resolved_at = datetime.utcnow()

    db.commit()

    return {
        "message": "Comment marked as resolved",
        "comment": comment.to_dict()
    }


@router.delete("/comments/{comment_id}")
async def delete_comment(
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete a comment (only by author or document owner)."""
    comment = db.query(DocumentComment).filter(DocumentComment.id == comment_id).first()

    if not comment:
        raise HTTPException(404, "Comment not found")

    # Check permission (author or document owner)
    document = db.query(Document).filter(Document.id == comment.document_id).first()
    if comment.author_id != current_user.id and document.user_id != current_user.id:
        raise HTTPException(403, "You don't have permission to delete this comment")

    db.delete(comment)
    db.commit()

    return {"message": "Comment deleted successfully"}
```

### 3. Collaboration API

```python
# backend/src/api/collaboration.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..core.database import get_db
from ..models.document import Document
from ..models.collaboration_invite import CollaborationInvite, InviteStatus, PermissionLevel
from ..models.document_access import DocumentAccess
from ..models.user import User
from ..core.security import get_current_user
from pydantic import BaseModel
from datetime import datetime

router = APIRouter()


class InviteRequest(BaseModel):
    email: str
    permission: str = PermissionLevel.EDITOR.value


class RespondToInviteRequest(BaseModel):
    accept: bool


@router.post("/documents/{document_id}/invite")
async def invite_collaborator(
    document_id: int,
    request: InviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Invite a user to collaborate on a document.

    Process:
    1. Find user by email
    2. Check for existing pending invites
    3. Create invite
    4. (Future) Send email notification
    """
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")

    # Check permission (only owner can invite)
    if document.user_id != current_user.id:
        raise HTTPException(403, "Only the document owner can invite collaborators")

    # Find invited user
    invited_user = db.query(User).filter(User.email == request.email).first()
    if not invited_user:
        raise HTTPException(404, f"User with email '{request.email}' not found")

    # Check for existing pending invite
    existing = db.query(CollaborationInvite).filter(
        CollaborationInvite.document_id == document_id,
        CollaborationInvite.invited_user_id == invited_user.id,
        CollaborationInvite.status == InviteStatus.PENDING.value
    ).first()

    if existing:
        raise HTTPException(400, "Pending invitation already exists for this user")

    # Check if user already has access
    existing_access = db.query(DocumentAccess).filter(
        DocumentAccess.document_id == document_id,
        DocumentAccess.user_id == invited_user.id
    ).first()

    if existing_access:
        raise HTTPException(400, "User already has access to this document")

    # Validate permission level
    if request.permission not in [p.value for p in PermissionLevel]:
        raise HTTPException(400, f"Invalid permission level. Must be one of: {[p.value for p in PermissionLevel]}")

    # Create invite
    invite = CollaborationInvite(
        document_id=document_id,
        invited_by=current_user.id,
        invited_user_id=invited_user.id,
        permission=request.permission
    )

    db.add(invite)
    db.commit()
    db.refresh(invite)

    # TODO: Send email notification

    return {
        "message": f"Invitation sent to {request.email}",
        "invite": invite.to_dict()
    }


@router.get("/invites")
async def list_invites(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List invitations for current user.

    Query params:
    - status: Filter by status (pending, accepted, declined, revoked)
    """
    query = db.query(CollaborationInvite).filter(
        CollaborationInvite.invited_user_id == current_user.id
    )

    if status:
        query = query.filter(CollaborationInvite.status == status)

    invites = query.order_by(CollaborationInvite.created_at.desc()).all()

    return {
        "total_invites": len(invites),
        "invites": [invite.to_dict() for invite in invites]
    }


@router.get("/documents/{document_id}/invites")
async def list_document_invites(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all invitations for a specific document (owner only)."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    invites = db.query(CollaborationInvite).filter(
        CollaborationInvite.document_id == document_id
    ).order_by(CollaborationInvite.created_at.desc()).all()

    return {
        "document_id": document_id,
        "total_invites": len(invites),
        "invites": [invite.to_dict() for invite in invites]
    }


@router.post("/invites/{invite_id}/respond")
async def respond_to_invite(
    invite_id: int,
    request: RespondToInviteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Accept or decline a collaboration invitation.

    When accepting:
    1. Updates invite status
    2. Creates DocumentAccess record
    """
    invite = db.query(CollaborationInvite).filter(
        CollaborationInvite.id == invite_id,
        CollaborationInvite.invited_user_id == current_user.id
    ).first()

    if not invite:
        raise HTTPException(404, "Invite not found")

    if invite.status != InviteStatus.PENDING.value:
        raise HTTPException(400, f"Invite already {invite.status}")

    if request.accept:
        # Accept invite
        invite.status = InviteStatus.ACCEPTED.value
        invite.accepted_at = datetime.utcnow()

        # Create access record
        access = DocumentAccess(
            document_id=invite.document_id,
            user_id=current_user.id,
            permission=invite.permission,
            granted_by=invite.invited_by
        )
        db.add(access)

        message = "Invitation accepted"
    else:
        # Decline invite
        invite.status = InviteStatus.DECLINED.value
        message = "Invitation declined"

    db.commit()

    return {
        "message": message,
        "invite": invite.to_dict()
    }


@router.delete("/invites/{invite_id}")
async def revoke_invite(
    invite_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Revoke a pending invitation (owner only)."""
    invite = db.query(CollaborationInvite).filter(
        CollaborationInvite.id == invite_id
    ).first()

    if not invite:
        raise HTTPException(404, "Invite not found")

    # Check permission (document owner)
    document = db.query(Document).filter(Document.id == invite.document_id).first()
    if document.user_id != current_user.id:
        raise HTTPException(403, "Only the document owner can revoke invitations")

    invite.status = InviteStatus.REVOKED.value
    db.commit()

    return {"message": "Invitation revoked"}


@router.get("/documents/{document_id}/collaborators")
async def list_collaborators(
    document_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all users with access to a document."""
    document = db.query(Document).filter(Document.id == document_id).first()
    if not document:
        raise HTTPException(404, "Document not found")

    # Get owner + collaborators
    access_records = db.query(DocumentAccess).filter(
        DocumentAccess.document_id == document_id
    ).all()

    collaborators = [
        {
            "user_id": document.user_id,
            "username": document.owner.username if document.owner else "Unknown",
            "email": document.owner.email if document.owner else "",
            "permission": "owner",
            "granted_at": document.created_at.isoformat()
        }
    ]

    for access in access_records:
        collaborators.append({
            "user_id": access.user_id,
            "username": access.user.username if access.user else "Unknown",
            "email": access.user.email if access.user else "",
            "permission": access.permission,
            "granted_at": access.granted_at.isoformat(),
            "granted_by": access.granter.username if access.granter else "Unknown"
        })

    return {
        "document_id": document_id,
        "total_collaborators": len(collaborators),
        "collaborators": collaborators
    }


@router.delete("/documents/{document_id}/collaborators/{user_id}")
async def remove_collaborator(
    document_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Remove a collaborator's access to a document (owner only)."""
    document = db.query(Document).filter(
        Document.id == document_id,
        Document.user_id == current_user.id
    ).first()

    if not document:
        raise HTTPException(404, "Document not found")

    # Find access record
    access = db.query(DocumentAccess).filter(
        DocumentAccess.document_id == document_id,
        DocumentAccess.user_id == user_id
    ).first()

    if not access:
        raise HTTPException(404, "Collaborator not found")

    db.delete(access)
    db.commit()

    return {"message": "Collaborator removed successfully"}
```

### 4. WebSocket for Real-time Collaboration

```python
# backend/src/api/collaboration_websocket.py

from fastapi import WebSocket, WebSocketDisconnect, Depends
from sqlalchemy.orm import Session
from typing import Dict, Set
import json
import logging
from ..core.database import SessionLocal
from ..models.collaboration_session import CollaborationSession
from ..models.user import User
from ..core.security import get_current_user_ws

logger = logging.getLogger(__name__)


class CollaborationManager:
    """
    Manages active WebSocket connections for real-time collaboration.

    Features:
    - Track active users per document
    - Broadcast events to all connected users
    - Handle presence (who's viewing/editing)
    """

    def __init__(self):
        # document_id -> {user_id -> WebSocket}
        self._connections: Dict[int, Dict[int, WebSocket]] = {}

        # document_id -> set of user_ids
        self._active_users: Dict[int, Set[int]] = {}

    async def connect(self, document_id: int, user_id: int, websocket: WebSocket):
        """Connect a user to a document collaboration session."""
        if document_id not in self._connections:
            self._connections[document_id] = {}
            self._active_users[document_id] = set()

        self._connections[document_id][user_id] = websocket
        self._active_users[document_id].add(user_id)

        logger.info(f"User {user_id} connected to document {document_id}")

        # Broadcast user joined event
        await self.broadcast(document_id, {
            "type": "user_joined",
            "user_id": user_id,
            "active_users": list(self._active_users[document_id])
        }, exclude_user_id=user_id)

    async def disconnect(self, document_id: int, user_id: int):
        """Disconnect a user from a document."""
        if document_id in self._connections:
            self._connections[document_id].pop(user_id, None)
            self._active_users[document_id].discard(user_id)

            logger.info(f"User {user_id} disconnected from document {document_id}")

            # Broadcast user left event
            await self.broadcast(document_id, {
                "type": "user_left",
                "user_id": user_id,
                "active_users": list(self._active_users[document_id])
            })

            # Clean up if no users left
            if not self._connections[document_id]:
                del self._connections[document_id]
                del self._active_users[document_id]

    async def broadcast(self, document_id: int, message: dict, exclude_user_id: int = None):
        """Broadcast a message to all users connected to a document."""
        if document_id not in self._connections:
            return

        for user_id, websocket in self._connections[document_id].items():
            if exclude_user_id and user_id == exclude_user_id:
                continue

            try:
                await websocket.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to user {user_id}: {e}")

    def get_active_users(self, document_id: int) -> Set[int]:
        """Get set of active user IDs for a document."""
        return self._active_users.get(document_id, set())


# Global singleton
_manager: CollaborationManager = None


def get_collaboration_manager() -> CollaborationManager:
    """Get or create the global collaboration manager singleton."""
    global _manager
    if _manager is None:
        _manager = CollaborationManager()
    return _manager


@router.websocket("/ws/documents/{document_id}/collaborate")
async def collaboration_websocket(
    document_id: int,
    websocket: WebSocket,
    token: str = None
):
    """
    WebSocket endpoint for real-time collaboration.

    Events:
    - cursor_move: Broadcast cursor position
    - comment_added: New comment notification
    - slide_updated: Slide change notification
    - user_joined/user_left: Presence tracking
    - typing: Typing indicator
    """
    manager = get_collaboration_manager()
    db = SessionLocal()

    # Authenticate user from token
    # (Simplified - implement proper token validation)
    try:
        # For now, we'll need a different auth approach for WebSocket
        # This is a placeholder showing the structure
        user_id = 1  # TODO: Get from token

        await websocket.accept()
        logger.info(f"WebSocket connected for document {document_id}")

        # Add to collaboration session
        await manager.connect(document_id, user_id, websocket)

        # Send current active users
        await websocket.send_json({
            "type": "connection_established",
            "document_id": document_id,
            "active_users": list(manager.get_active_users(document_id))
        })

        try:
            # Message loop
            while True:
                data = await websocket.receive_json()

                # Handle different message types
                event_type = data.get("type")

                if event_type == "cursor_move":
                    # Broadcast cursor position to other users
                    await manager.broadcast(document_id, {
                        "type": "cursor_move",
                        "user_id": user_id,
                        "slide_number": data.get("slide_number"),
                        "x": data.get("x"),
                        "y": data.get("y")
                    }, exclude_user_id=user_id)

                elif event_type == "typing":
                    # Broadcast typing indicator
                    await manager.broadcast(document_id, {
                        "type": "typing",
                        "user_id": user_id,
                        "slide_number": data.get("slide_number")
                    }, exclude_user_id=user_id)

                elif event_type == "comment_added":
                    # Broadcast new comment notification
                    await manager.broadcast(document_id, {
                        "type": "comment_added",
                        "user_id": user_id,
                        "comment_id": data.get("comment_id"),
                        "slide_number": data.get("slide_number")
                    })

                elif event_type == "slide_updated":
                    # Broadcast slide update notification
                    await manager.broadcast(document_id, {
                        "type": "slide_updated",
                        "user_id": user_id,
                        "slide_number": data.get("slide_number"),
                        "update_type": data.get("update_type")  # "content", "demo", etc.
                    }, exclude_user_id=user_id)

                elif event_type == "ping":
                    # Keep connection alive
                    await websocket.send_json({"type": "pong"})

        except WebSocketDisconnect:
            logger.info(f"WebSocket disconnected for document {document_id}")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
        finally:
            # Clean up
            await manager.disconnect(document_id, user_id)

    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
        await websocket.close()
    finally:
        db.close()
```

## Frontend Components

### Version History Component

```typescript
// frontend/src/components/collaboration/VersionHistory.tsx

import React, { useState, useEffect } from 'axios';

interface Version {
  id: number;
  version_number: number;
  created_at: string;
  created_by: string;
  change_summary: string;
  change_type: string;
  slide_count: number;
}

interface VersionHistoryProps {
  documentId: number;
  onRestore?: (versionNumber: number) => void;
}

export const VersionHistory: React.FC<VersionHistoryProps> = ({ documentId, onRestore }) => {
  const [versions, setVersions] = useState<Version[]>([]);
  const [selectedVersion, setSelectedVersion] = useState<Version | null>(null);
  const [loading, setLoading] = useState(true);
  const [restoring, setRestoring] = useState(false);

  useEffect(() => {
    fetchVersions();
  }, [documentId]);

  const fetchVersions = async () => {
    setLoading(true);
    try {
      const response = await axios.get(`/api/collaboration/documents/${documentId}/versions`);
      setVersions(response.data.versions);
    } catch (error) {
      console.error('Failed to fetch versions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleRestore = async (versionNumber: number) => {
    if (!confirm('Are you sure you want to restore to this version? A backup of the current version will be created automatically.')) {
      return;
    }

    setRestoring(true);
    try {
      const reason = prompt('Reason for restoration (optional):');
      await axios.post(`/api/collaboration/documents/${documentId}/versions/${versionNumber}/restore`, {
        change_summary: reason || undefined
      });

      alert('Version restored successfully!');
      fetchVersions();
      onRestore?.(versionNumber);
    } catch (error) {
      console.error('Failed to restore version:', error);
      alert('Failed to restore version');
    } finally {
      setRestoring(false);
    }
  };

  const getChangeTypeIcon = (type: string) => {
    const icons = {
      'initial': '🆕',
      'ui_modification': '🎨',
      'slide_update': '📄',
      'content_edit': '✏️',
      'restore': '↩️',
      'restore_backup': '💾'
    };
    return icons[type] || '📝';
  };

  if (loading) {
    return <div className="version-history loading">Loading version history...</div>;
  }

  return (
    <div className="version-history">
      <h3>Version History</h3>
      <p className="version-count">{versions.length} versions</p>

      <div className="version-list">
        {versions.map((version, index) => (
          <div
            key={version.id}
            className={`version-item ${selectedVersion?.id === version.id ? 'selected' : ''}`}
            onClick={() => setSelectedVersion(version)}
          >
            <div className="version-header">
              <span className="version-number">v{version.version_number}</span>
              <span className="version-icon">{getChangeTypeIcon(version.change_type)}</span>
              <span className="version-date">
                {new Date(version.created_at).toLocaleString()}
              </span>
            </div>

            <div className="version-summary">{version.change_summary}</div>

            <div className="version-meta">
              <span className="version-author">by {version.created_by}</span>
              <span className="version-slides">{version.slide_count} slides</span>
            </div>

            {index > 0 && ( // Can't restore the latest version
              <button
                className="restore-button"
                onClick={(e) => {
                  e.stopPropagation();
                  handleRestore(version.version_number);
                }}
                disabled={restoring}
              >
                {restoring ? 'Restoring...' : 'Restore'}
              </button>
            )}
          </div>
        ))}
      </div>

      {selectedVersion && (
        <div className="version-details">
          <h4>Version Details</h4>
          <dl>
            <dt>Version:</dt>
            <dd>{selectedVersion.version_number}</dd>

            <dt>Created:</dt>
            <dd>{new Date(selectedVersion.created_at).toLocaleString()}</dd>

            <dt>Author:</dt>
            <dd>{selectedVersion.created_by}</dd>

            <dt>Type:</dt>
            <dd>{selectedVersion.change_type}</dd>

            <dt>Summary:</dt>
            <dd>{selectedVersion.change_summary}</dd>

            <dt>Slides:</dt>
            <dd>{selectedVersion.slide_count}</dd>
          </dl>
        </div>
      )}
    </div>
  );
};
```

### Comments Panel Component

```typescript
// frontend/src/components/collaboration/CommentsPanel.tsx

import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface Comment {
  id: number;
  slide_number: number | null;
  content: string;
  comment_type: string;
  author: string;
  created_at: string;
  is_resolved: boolean;
  replies?: Comment[];
  reply_count: number;
}

interface CommentsPanelProps {
  documentId: number;
  slideNumber?: number;
}

export const CommentsPanel: React.FC<CommentsPanelProps> = ({ documentId, slideNumber }) => {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchComments();
  }, [documentId, slideNumber]);

  const fetchComments = async () => {
    setLoading(true);
    try {
      const url = slideNumber !== undefined
        ? `/api/collaboration/documents/${documentId}/comments?slide_number=${slideNumber}`
        : `/api/collaboration/documents/${documentId}/comments`;

      const response = await axios.get(url);
      setComments(response.data.comments);
    } catch (error) {
      console.error('Failed to fetch comments:', error);
    } finally {
      setLoading(false);
    }
  };

  const submitComment = async () => {
    if (!newComment.trim()) return;

    try {
      await axios.post(`/api/collaboration/documents/${documentId}/comments`, {
        content: newComment,
        slide_number: slideNumber,
        comment_type: 'suggestion'
      });

      setNewComment('');
      fetchComments();
    } catch (error) {
      console.error('Failed to submit comment:', error);
      alert('Failed to submit comment');
    }
  };

  const resolveComment = async (commentId: number) => {
    try {
      await axios.put(`/api/collaboration/comments/${commentId}/resolve`);
      fetchComments();
    } catch (error) {
      console.error('Failed to resolve comment:', error);
    }
  };

  const getCommentTypeIcon = (type: string) => {
    const icons = {
      'suggestion': '💡',
      'question': '❓',
      'issue': '⚠️',
      'praise': '👍'
    };
    return icons[type] || '💬';
  };

  return (
    <div className="comments-panel">
      <h3>{slideNumber !== undefined ? `Comments on Slide ${slideNumber}` : 'Document Comments'}</h3>

      {/* New comment form */}
      <div className="new-comment">
        <textarea
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          placeholder="Add a comment..."
          rows={3}
        />
        <button onClick={submitComment} disabled={!newComment.trim()}>
          Add Comment
        </button>
      </div>

      {/* Comments list */}
      {loading ? (
        <div className="loading">Loading comments...</div>
      ) : comments.length === 0 ? (
        <div className="no-comments">No comments yet. Be the first to comment!</div>
      ) : (
        <div className="comments-list">
          {comments.map((comment) => (
            <CommentItem
              key={comment.id}
              comment={comment}
              onResolve={resolveComment}
            />
          ))}
        </div>
      )}
    </div>
  );
};

const CommentItem: React.FC<{
  comment: Comment;
  onResolve: (commentId: number) => void;
}> = ({ comment, onResolve }) => {
  const [showReplies, setShowReplies] = useState(false);

  return (
    <div className={`comment-item ${comment.is_resolved ? 'resolved' : ''}`}>
      <div className="comment-header">
        <span className="comment-icon">{getCommentTypeIcon(comment.comment_type)}</span>
        <span className="comment-author">{comment.author}</span>
        <span className="comment-date">
          {new Date(comment.created_at).toLocaleString()}
        </span>
      </div>

      <div className="comment-content">{comment.content}</div>

      <div className="comment-actions">
        {!comment.is_resolved && (
          <button onClick={() => onResolve(comment.id)}>
            ✓ Resolve
          </button>
        )}

        {comment.reply_count > 0 && (
          <button onClick={() => setShowReplies(!showReplies)}>
            {showReplies ? 'Hide' : 'Show'} {comment.reply_count} {comment.reply_count === 1 ? 'reply' : 'replies'}
          </button>
        )}
      </div>

      {showReplies && comment.replies && (
        <div className="comment-replies">
          {comment.replies.map((reply) => (
            <CommentItem key={reply.id} comment={reply} onResolve={() => {}} />
          ))}
        </div>
      )}
    </div>
  );
};
```

## Implementation Timeline

### Phase 1: Database & Backend API (Week 1-2)
- [ ] Create database migration with all models
- [ ] Implement version management endpoints
- [ ] Implement comments API
- [ ] Implement collaboration invites API
- [ ] Write unit tests for all endpoints

### Phase 2: WebSocket Real-time Features (Week 3)
- [ ] Implement WebSocket server
- [ ] Build collaboration manager
- [ ] Add presence tracking
- [ ] Implement event broadcasting

### Phase 3: Frontend Components (Week 3-4)
- [ ] Version history UI
- [ ] Comments panel component
- [ ] Collaboration invite UI
- [ ] Real-time presence indicators
- [ ] WebSocket integration

### Phase 4: Testing & Polish (Week 5)
- [ ] End-to-end testing
- [ ] Permission testing
- [ ] UI/UX improvements
- [ ] Documentation

## Success Metrics

- **Collaboration rate**: 30%+ of documents shared with at least one collaborator
- **Comment usage**: 50%+ of collaborative documents have comments
- **Version restore**: 10%+ of documents have version history restored at least once
- **User satisfaction**: 4.5+ star rating on collaboration features
- **Content reuse**: 25%+ reduction in duplicate content creation
