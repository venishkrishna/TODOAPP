from fastapi import APIRouter, Depends, HTTPException, Path
from typing import Annotated
from sqlalchemy.orm import session
from models import Todos
from database import engine, SessionLocal
from starlette import status
from pydantic import BaseModel, Field
from .auth import get_current_user


router= APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
db_dependency= Annotated[session, Depends(get_db)]

user_dependency = Annotated[dict, Depends(get_current_user)]

class TodoRequest(BaseModel):
    title : str = Field(min_length= 3)
    description : str = Field(min_length= 6)
    priority : int = Field(gt=0)
    complete : bool

@router.get("/")
async def read_all(user: user_dependency,db: db_dependency):
    if user is None:
        raise HTTPException(status_code=401)
    return db.query(Todos).filter(Todos.owner_id == user.get('id')).all()

@router.get("/todo/{todo_id}", status_code= status.HTTP_200_OK)
async def read_todo(user: user_dependency,db: db_dependency, todo_id: int = Path(gt=0)):
    if user is None:
        raise HTTPException(status_code=401)
    todo_model = db.query(Todos).filter(Todos.id==todo_id and Todos.owner_id == user.get('id')).first()
    if todo_model is not None:
        return todo_model
    raise HTTPException(status_code= 404, detail= "Todo not found")

@router.post("/todo/add_todo/", status_code=status.HTTP_201_CREATED)
async def Add_todo(user: user_dependency,db: db_dependency,
                   new: TodoRequest):

    if user is None:
        raise HTTPException(status_code=401)
    new_todo = Todos(**new.model_dump(),owner_id = user.get('id'))
    db.add(new_todo)
    db.commit()

@router.put("/todo/edit_todo/{todo_id}")
async def edit_todo(user: user_dependency,db: db_dependency, todo_id: int, todo_request: TodoRequest ):
    if user is None:
        raise HTTPException(status_code=401)
    new = db.query(Todos).filter(Todos.id == todo_id and Todos.owner_id == user.get('id')).first()
    if new is None:
        raise HTTPException(status_code=404, detail="Todo not found")

    new.title= todo_request.title
    new.description = todo_request.description
    new.priority = todo_request.priority
    new.complete = todo_request.complete

    db.add(new)
    db.commit()


@router.delete("/todo/delete_todo/{todo_id}")
async def delete_todo(user : user_dependency,db: db_dependency , todo_id: int):
    if user is None:
        raise HTTPException(status_code=401)
    remove_todo= db.query(Todos).filter(Todos.id == todo_id and Todos.owner_id == user.get('id')).first()
    if remove_todo is None:
        raise HTTPException(status_code=404 , detail="Todo not found")
    db.query(Todos).filter(Todos.id == todo_id and Todos.owner_id == user.get('id')).delete()

    db.commit()

