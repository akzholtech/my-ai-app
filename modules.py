from typing import List

import numpy as np

from database import Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Index, LargeBinary
from sqlalchemy.orm import relationship, Mapped, mapped_column, Session


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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    external_id: Mapped[str] = mapped_column(String(128), unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(256))

    templates: Mapped[List["Template"]] = relationship(back_populates="person", cascade="all, delete-orphan")


class Template(Base):
    __tablename__ = 'templates'

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    person_id: Mapped[int] = mapped_column(ForeignKey("people.id", ondelete="CASCADE"))
    vec: Mapped[bytes] = mapped_column(LargeBinary)
    dim: Mapped[int] = mapped_column(Integer, default=512)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    person: Mapped[Person] = relationship(back_populates="templates")


def add_person(session: Session, external_id: str, display_name: str) -> Person:
    p = Person(external_id=external_id, display_name=display_name)
    session.add(p); session.commit(); session.refresh(p)
    return p

def get_person_by_external_id(session: Session, external_id: str) -> Person | None:
    return session.query(Person).filter_by(external_id=external_id).one_or_none()

def add_template(session: Session, person: Person, emb: np.ndarray) -> Template:
    t = Template(vec=emb.tobytes(), dim=emb.shape[0], person_id=person.id)
    session.add(t); session.commit(); session.refresh(t)
    return t

def load_person_templates(session: Session, person: Person) -> np.ndarray:
    rows = session.query(Template).filter_by(person_id=person.id).all()
    if not rows: return np.empty((0, 512), dtype=np.float32)
    arrays = [np.frombuffer(r.vec, dtype=np.float32)[:r.dim] for r in rows]
    return np.vstack(arrays)

def np_to_blob(arr: np.ndarray) -> bytes:
    a = np.asarray(arr, dtype=np.float32)
    return a.tobytes(order='C')

def blob_to_np(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32)