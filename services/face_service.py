from typing import Tuple, List
from PIL import Image
import io
import numpy as np
from insightface.app import FaceAnalysis


class ArcFaceEngine:
    def __init__(self, det_size: Tuple[int, int]=(640, 640), providers=None):
        self.app = FaceAnalysis(name="buffalo_l", providers=providers)
        self.app.prepare(ctx_id=0, det_size=det_size)


    @staticmethod
    def _pil_from_bytes(image_bytes: bytes) -> Image.Image:
        img = Image.open(io.BytesIO(image_bytes)).convert('RGB')
        return img

    def detect_and_embed(self, image_bytes: bytes) -> List[Tuple[np.ndarray, np.ndarray]]:
        """
        Returns list of (bbox_xyxy, embedding_512) for each detected face.
        """
        img = np.array(self._pil_from_bytes(image_bytes))
        faces = self.app.get(img) # each face has .bbox, .normed_embedding
        out = []
        for face in faces:
            emb = np.asarray(face.normed_embedding, dtype=np.float32)
            bbox = np.asarray(face.bbox, dtype=np.float32)
            out.append((bbox, emb))
        return out


    @staticmethod
    def cosine_distance(a: np.ndarray, b: np.ndarray) -> float:
        return 1 - float(np.dot(a, b))