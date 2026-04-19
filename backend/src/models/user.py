from sqlalchemy import Column, Integer, String, DateTime, Boolean, JSON
from sqlalchemy.sql import func
from src.core.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String)
    grade_level = Column(Integer, default=0)  # K-12, 0 for Kindergarten
    interests = Column(JSON, default=list)  # List of user interests
    learning_preferences = Column(JSON, default=dict)  # Learning preferences dict
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships will be added later to avoid circular imports

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', username='{self.username}')>"