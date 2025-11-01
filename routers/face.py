from fastapi import APIRouter
import io
import numpy as np
from PIL import Image
from insightface.app import FaceAnalysis

router = APIRouter()

_face_app = None

def init_models(det_name="buffalo_l", rec_size=(112, 112), providers=None):
    """
    :param det_name: "buffalo_l" loads RetinaFace + ArcFace-recognition pipline.
    """
    global _face_app
    _face_app = FaceAnalysis(name=det_name, providers=providers or ["CPUExecutionProvider"])
    _face_app.prepare(ctx_id=0, det_size=(640, 640))
    return _face_app

def _pil_from_bytes(b: bytes) -> Image.Image:
    return Image.open(io.BytesIO(b)).convert("RGB")

def extract_best_face_embedding(image_bytes: bytes):
    """
    :return: (embedding: np.ndarray[dim], quality_info: dict) or (None, {...})
    """
    global _face_app
    _face_app = init_models()
    img = np.array(_pil_from_bytes(image_bytes))[:,:,::-1]
    faces = _face_app.get(img)
    if not faces:
        return None, {"found": 0}

    # choose the largest face
    faces.sort(key=lambda f: (f.bbox[2]-f.bbox[0])*(f.bbox[3]-f.bbox[1]), reverse=True)
    f0 = faces[0]

    emb = f0.normed_embedding.astype(np.float32)
    return emb, {
        "found": len(faces),
        "bbox": list(map(float, f0.bbox)),
        "det_score": float(getattr(f0, "det_score", 0.0))
    }

def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
    return float(np.dot(a, b))










