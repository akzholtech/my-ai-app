from datetime import timedelta
from fastapi import APIRouter, Request, Depends, HTTPException, UploadFile, File, Form
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session
from typing import Annotated

from starlette import status

from services.config import ONNX_PROVIDERS
from .auth import get_current_user, user_authentication, create_access_token, Token
from modules import Base, get_person_by_external_id, add_person, add_template, load_person_templates
from database import engine, SessionLocal
from .face import init_models, extract_best_face_embedding

router = APIRouter()
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)
user_dependency = Annotated[dict, Depends(get_current_user)]

def get_db():
    db = SessionLocal()
    try: yield db
    finally: db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class UserLogin(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1)

class EnrollUser(BaseModel):
    person_id: int
    templates: int

###Pages###
@router.on_startup()
async def _startup():
    init_models(providers=ONNX_PROVIDERS)

@router.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

###Endpoints###

@router.post("/api/login", response_model=Token)
async def login(db: db_dependency, user_req: UserLogin):
    user = user_authentication(user_req.name, user_req.password, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Username or password incorrect!")

    token = create_access_token(user.username, user.id, user.role, expires_delta=timedelta(minutes=5))
    return {'access_token': token, 'token_type': 'bearer'}

@router.get("/enroll", response_model=EnrollUser)
async def enroll(image: UploadFile = File(...),
                 external_id: str = Form(...),
                 display_name: str = Form(""),
                 db: Session = db_dependency):
    person = get_person_by_external_id(db, external_id)
    if person is None:
        person = add_person(db, external_id, display_name or external_id)

    img_bytes = await image.read()
    emb, info = extract_best_face_embedding(img_bytes)
    if emb in None:
        raise HTTPException(status_code=404, detail="No face found")

    add_template(db, person, emb)
    total = load_person_templates(db, person).shape[0]
    return EnrollUser(person_id=person.id, templates=total)
