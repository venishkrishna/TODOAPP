from datetime import timedelta, datetime, timezone
#from http.client import HTTPException

from fastapi import APIRouter, Depends, HTTPException
from typing import Annotated
from pydantic import BaseModel
from sqlalchemy import false
from sqlalchemy.sql.coercions import expect

from database import SessionLocal
from sqlalchemy.orm import session
from models import Users
from passlib.context import CryptContext
from starlette import status
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt, JWTError
router = APIRouter(prefix='/auth',tags=['auth'])

SECRET_KEY = '0ZMsGfWLNy64k+xXHsNn3eD4Jzz+tZxJ5p5nc5dzMDw='
ALGORITHM = 'HS256'
bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = OAuth2PasswordBearer(tokenUrl='auth/token')

class CreateUserRequest(BaseModel):
    username : str
    email : str
    first_name : str
    last_name : str
    password : str
    role : str


class Token(BaseModel):
    access_token: str
    token_type: str

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency= Annotated[session, Depends(get_db)]

def authenticate_user(username: str,  password: str, db):
    user = db.query(Users).filter(Users.username == username).first()

    if not user:
        return False
    if not bcrypt_context.verify(password,user.hashed_password):
        return False
    return user

def create_access_token(username: str, user_id: int, expires_delta: timedelta):

    encode = {'sub': username, 'id': user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode,SECRET_KEY,algorithm= ALGORITHM)

async def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get('sub')
        user_id: int = payload.get('id')
        if username is None or user_id is None:
            raise HTTPException(status_code = status.HTTP_401_UNAUTHORIZED, detail= 'could not validate user')
        return {'username': username, 'id': user_id}
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='could not validate user')


@router.post("/register/", status_code= status.HTTP_201_CREATED)
async def create_user(db: db_dependency,new : CreateUserRequest):
    new_user = Users(
        email = new.email,
        username = new.username,
        first_name = new.first_name,
        last_name = new.last_name,
        role = new.role,
        hashed_password = bcrypt_context.hash(new.password),
        is_active= True
    )

    db.add(new_user)
    db.commit()

@router.post("/token", response_model= Token)
async def login_for_access_token(form_data: Annotated[OAuth2PasswordRequestForm,Depends()],db: db_dependency):

    user = authenticate_user(form_data.username,form_data.password, db)
    if not user:
        raise HTTPException(status_code= 401, detail= 'Failed Authentication')
    token = create_access_token(user.username , user.id, timedelta(minutes=20))

    return {'access_token': token, 'token_type':'bearer'}


