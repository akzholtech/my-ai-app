from datetime import timedelta

from fastapi import APIRouter, Request, Depends, Path, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session
from typing import Annotated

from starlette import status
from .auth import get_current_user, user_authentication, create_access_token, Token
from modules import Users, Base
from database import engine, SessionLocal

router = APIRouter()
templates = Jinja2Templates(directory="templates")

Base.metadata.create_all(bind=engine)
user_dependency = Annotated[dict, Depends(get_current_user)]

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class UserLogin(BaseModel):
    name: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1)

###Pages###

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
# @router.get("/run-recognition", response_class=HTMLResponse)
# async def run_recognition(request: Request, db: db_dependency):
#     async def event_generator():
#         gen = face_net.run_recognition()
#         try:
#             for frame in gen:
#                 if await request.is_disconnected():
#                     break
#                 yield frame
#         finally:
#             gen.close()
#     return StreamingResponse(event_generator(), media_type="multipart/x-mixed-replace; boundary=frame")