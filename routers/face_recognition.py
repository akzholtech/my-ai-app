from typing import List, Optional, Annotated

import numpy as np
from fastapi import APIRouter, Form, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel

from routers.auth import get_current_user
from services.face_service import ArcFaceEngine
from services.gallery_store import GalleryStore

router = APIRouter(prefix="/face", tags=["face"])

engine = ArcFaceEngine(det_size=(640, 640))
store = GalleryStore()

DEFAULT_THRESHOLD = 0.35
user_dependency = Annotated[dict, Depends(get_current_user)]

class RecognizedFace(BaseModel):
    name: str
    bbox: List[float]
    distance: float
    similarity: float

class RecognizeResponse(BaseModel):
    results: List[RecognizedFace]

@router.post("/enroll")
async def enroll(user: user_dependency, name: str = Form(...), image: UploadFile = File(...)):
    if user is None:
        raise HTTPException(status_code=404, detail="Authentication required!")

    content = await image.read()
    faces = engine.detect_and_embed(content)
    if not faces:
        raise HTTPException(status_code=404, detail="No face detected.")

    bboxes = np.array([f[0] for f in faces])
    areas = (bboxes[:, 2] - bboxes[:, 0]) * (bboxes[:, 3] - bboxes[:, 1])
    idx = int(np.argmax(areas))
    _, emb = faces[idx]

    store.add_embedding(name, emb)
    return {"ok": True, "name": name, "faces_detected": len(faces)}


@router.post("/recognize", response_model=RecognizeResponse)
async def recognize(image: UploadFile = File(...), threshold: Optional[float] = Form(None)):
    th = float(threshold) if threshold is not None else DEFAULT_THRESHOLD
    content = await image.read()
    faces = engine.detect_and_embed(content)
    if not faces:
        return {"results": []}

    gallery = store.all_embeddings()
    results = []
    for bbox, q_emb in faces:
        best_name = "unknown"
        best_distance = 1.0
        for name, emb in gallery:
            d = engine.cosine_distance(q_emb, emb)
            if d < best_distance:
                best_distance = d
                best_name = name
        if best_distance < th:
            results.append(RecognizedFace(name=best_name,
                                          bbox=bbox.tolist(),
                                          distance=float(best_distance),
                                          similarity=float(1.0 - best_distance)))
        else:
            results.append(RecognizedFace(name="unknown",
                                          bbox=bbox.tolist(),
                                          distance=float(best_distance),
                                          similarity=float(1.0 - best_distance)))

    return {"results": results}

@router.get("/gallery")
async def get_gallery(user: user_dependency):
    if user is None:
        raise HTTPException(status_code=404, detail="Authentication required!")
    return {"Identities": store.list_identities()}

@router.delete("/gallery/{name}")
async def delete_identity(user: user_dependency , name: str):
    if user is None:
        raise HTTPException(status_code=404, detail="Authentication required!")
    ok = store.delete_identity(name)
    if not ok:
        raise HTTPException(status_code=404, detail="No identity found.")
    return {"ok": ok, "deleted": name}

