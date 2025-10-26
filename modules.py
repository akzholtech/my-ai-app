import numpy as np

from database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, LargeBinary
from sqlalchemy.orm import relationship


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    role = Column(String)
    embedding = Column(String)

class Person (Base):
    __tablename__ = 'people'
    id = Column(Integer, primary_key=True)
    name = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now)
    embeddings = relationship("FaceEmbedding", back_populates="person", cascade="all, delete-orphan")

class FaceEmbedding(Base):
    __tablename__ = 'embeddings'
    id = Column(Integer, primary_key=True)
    person_id = Column(Integer, ForeignKey('people.id', ondelete='CASCADE'), nullable=False)
    vector = Column(LargeBinary, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)

    person = relationship("Person", back_populates="embeddings")

# Index("ix_embeddings_person_created")

def np_to_blob(arr: np.ndarray) -> bytes:
    a = np.asarray(arr, dtype=np.float32)
    return a.tobytes(order='C')

def blob_to_np(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)