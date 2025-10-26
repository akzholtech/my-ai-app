from contextlib import contextmanager
from dataclasses import dataclass
from typing import List, Tuple
import numpy as np
from sqlalchemy.orm import Session, sessionmaker
from database import engine, SessionLocal
from modules import Person, np_to_blob, FaceEmbedding, blob_to_np


@dataclass
class Identity:
    name: str
    embeddings: List[List[float]]

class GalleryStore:
    def __init__(self):
        self.SessionLocal: sessionmaker[Session] = SessionLocal

    @contextmanager
    def _session(self):
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def list_identities(self) -> List[str]:
        with self._session() as s:
            return [p.name for p in s.query(Person).order_by(Person.name.asc()).all()]

    def add_embedding(self, name: str, emb: np.ndarray):
        with self._session() as s:
            person = s.query(Person).filter_by(name=name).one_or_none()
            if person is None:
                person = Person(name=name)
                s.add(person)
                s.flush()
            vec_blob = np_to_blob(emb)
            s.add(FaceEmbedding(person_id=person.id, vector=vec_blob))

    def delete_identity(self, name: str) -> bool:
        with self._session() as s:
            person = s.query(Person).filter_by(name=name).one_or_none()
            if person is None:
                return False
            s.delete(person)
            return True


    def all_embeddings(self) -> List[Tuple[str, np.ndarray]]:
        with self._session() as s:
            p = (s.query(Person.name, FaceEmbedding.vector)
                 .join(FaceEmbedding, FaceEmbedding.person_id == Person.id))
            rows = p.all()
            return [(name, blob_to_np(vec)) for (name, vec) in rows]