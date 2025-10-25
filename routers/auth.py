from typing import Annotated
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from sqlalchemy.orm import Session
from starlette import status
from starlette.responses import RedirectResponse

from database import SessionLocal
from modules import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()
SECRET_KEY = '286d960fdff634715693d16de0f1ccc49af84a5dfb3075f55e0b73cbe5cca9ca'
ALGORITHM = 'HS256'

oauth2_scheme = OAuth2PasswordBearer(tokenUrl='auth/token')
pwd_context = CryptContext(schemes=['bcrypt'], deprecated='auto')

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

class Token(BaseModel):
    access_token: str
    token_type: str

class UserRequest(BaseModel):
    username: str
    password: str
    first_name: str
    last_name: str
    email: str
    role: str
    embedding: str

def user_authentication(username: str, password: str, db):
    user_auth = db.query(Users).filter(Users.username == username).first()
    if not user_auth:
        return False
    elif not pwd_context.verify(password, user_auth.hashed_password):
        return False
    else:
        return user_auth

def create_access_token(username: str, user_id: int, user_role: str,  expires_delta: timedelta):
    encode: dict = {'sub': username, 'id': user_id, 'role': user_role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=ALGORITHM)
        username = payload.get('sub')
        user_id = payload.get('id')
        user_role = payload.get('role')
        if username is None or user_id is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user')
        return {'username': username, 'id': user_id, 'role': user_role}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='JWT error occurred')

users_dependency = Annotated[dict, Depends(get_current_user)]

### Endpoints

@router.get('/users')
async def get_users(user_dto: users_dependency, db: Session = Depends(get_db)):
    if user_dto is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized in auth')

    users = db.query(Users).all()
    return {'users': users}

@router.post("/create", status_code=status.HTTP_200_OK)
async def login(user_dto: users_dependency, db: db_dependency, new_user: UserRequest):
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
    db.refresh(user_model)

@router.post("/token", response_model=Token)
async def login_for_access_token(user_dto: users_dependency, form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
                                 db: db_dependency):
    if user_dto is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Not authenticated')

    user = user_authentication(form_data.username, form_data.password, db)

    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect username or password')

    token = create_access_token(user.username, user.id, user.role, expires_delta=timedelta(minutes=10))

    return {'access_token': token, 'token_type': 'bearer'}

@router.get("/verify-token")
def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return {"user": payload["sub"]}
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
