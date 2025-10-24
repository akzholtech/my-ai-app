from fastapi import APIRouter, Request, Depends, Path, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from fastapi.responses import StreamingResponse
from pydantic import Field, BaseModel
from sqlalchemy.orm import Session
from typing import Annotated

from starlette import status
from .auth import get_current_user
from services import face_net
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

@router.get("/")
async def root(request: Request, db: db_dependency):
    return db.query(Users).all()
    # return templates.TemplateResponse('index.html', context={'request': request})


@router.get("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async  def get_todo_by_id(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_item = db.query(Users).filter(Users.id == todo_id).first()
    if todo_item is not None:
        return todo_item
    raise HTTPException(status_code=404, detail="todo not found")


@router.post("/todo", status_code=status.HTTP_201_CREATED)
async def create_todo(user: user_dependency,
                      db: db_dependency, todo: UserLogin):
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Could not validate credentials")

    todo_model = Users(**todo.model_dump())
    db.add(todo_model)
    db.commit()

@router.put("/todo/{todo_id}", status_code=status.HTTP_200_OK)
async def update_data(db: db_dependency, todo: UserLogin, todo_id: int = Path(gt=0)):
    todo_item = db.query(Users).filter(Users.id == todo_id).first()
    if todo_item is None:
        raise HTTPException(status_code=404, detail="not found item by the id")
    todo_item.name = todo.name
    todo_item.password = todo.password
    db.add(todo_item)
    db.commit()

@router.delete("todo/{todo_id}", status_code=status.HTTP_200_OK)
async def delete_todo(db: db_dependency, todo_id: int = Path(gt=0)):
    todo_item = db.query(Users).filter(Users.id == todo_id).first()
    if todo_item is None:
        raise HTTPException(status_code=404, detail="not found item by the id")
    db.query(Users).filter(Users.id == todo_id).delete()
    db.commit()
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