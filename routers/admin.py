from fastapi import APIRouter, HTTPException, Depends, Request
from passlib.context import CryptContext
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import List, Annotated
from routers.auth import get_current_user
from database import SessionLocal
from modules import Users

router = APIRouter(prefix="/admin", tags=["admin"])
templates = Jinja2Templates(directory="templates")
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

DEFAULT_THRESHOLD = 0.35
user_dependency = Annotated[dict, Depends(get_current_user)]

RT_THRESHOLD = 0.32

class RecognizedFace(BaseModel):
    name: str
    bbox: List[float]
    distance: float
    similarity: float

class RecognizeResponse(BaseModel):
    results: List[RecognizedFace]

class UserRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1)
    first_name: str = Field(min_length=1)
    last_name: str = Field(min_length=1)
    email: str = Field(min_length=1)
    role: str = Field(min_length=1)



### Pages ###
@router.get("/", response_class=HTMLResponse)
async def get_admin_page(request: Request) -> HTMLResponse:
    return templates.TemplateResponse("admin.html", context={"request": request})

### Endpoints ###
@router.post("/create", status_code=status.HTTP_200_OK)
async def login(user_dto: user_dependency, db: db_dependency, new_user: UserRequest):
    if user_dto is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user_model = Users(
        username=new_user.username,
        hashed_password=pwd_context.hash(new_user.password),
        email=new_user.email,
        first_name=new_user.first_name,
        last_name=new_user.last_name,
        role=new_user.role,
    )
    db.add(user_model)
    db.commit()
