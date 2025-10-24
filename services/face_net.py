from typing import Annotated
from facenet_pytorch import InceptionResnetV1, MTCNN
import cv2
import torch
from fastapi.params import Depends
from numpy.linalg import norm
from sqlalchemy.orm import Session

from database import SessionLocal

mtcnn = MTCNN()
facenet = InceptionResnetV1(pretrained='vggface2').eval()
known_faces = []

def get_bd():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_faces_fr_db(db: Annotated[Session, Depends(get_bd)]):
    global known_faces
    known_faces = db.query(facenet).all()


def get_embedding(img):
    face = cv2.resize(img, (160, 160))
    face_tensor = torch.tensor(face).permute(2, 0, 1).unsqueeze(0).float()/255.0
    return facenet(face_tensor).detach().numpy()


def compare_embeddings(emb1, emb2, threshold=1.0):
    distance = norm(emb1 - emb2)
    return distance < threshold, distance


def run_recognition():
    cap = cv2.VideoCapture(0)
    try:
        while True:
            ret, frame = cap.read()
            frame = cv2.flip(frame, 1)
            if not ret:
                break
            else:
                img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                boxes, _ = mtcnn.detect(img_rgb)

                if boxes is not None:
                    for box in boxes:
                        x1, y1, x2, y2 = map(int, box)
                        face = img_rgb[y1:y2, x1:x2]
                        if face.size == 0:
                            continue
                        embedding = get_embedding(face)
                        name = 'Unknown'

                        for person, emb in known_faces:
                            same, dis = compare_embeddings(embedding, emb)
                            if same:
                                name = person
                                break
                        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                        cv2.putText(frame, name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)

                ret, buffer = cv2.imencode('.jpg', frame)
                frame = buffer.tobytes()

                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
    finally:
        cap.release()
        cv2.destroyAllWindows()