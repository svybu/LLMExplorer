from typing import List

from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy.orm import Session

from api.conf.messages import ERROR_USER_NOT_FOUND
from api.database.db import get_db
from api.database.models import User
from api.repository.users import get_users, get_user_by_id, update
from api.schemas import UserUpdate, UserDb
from api.services.auth import auth_service

router = APIRouter(prefix='/users', tags=["Profile"])


@router.get("/", response_model=List[UserDb])
async def get_users_list(db: Session = Depends(get_db)):
    return await get_users(db)


@router.get("/{user_id}/", response_model=UserDb)
async def get_user(user_id: int, db: Session = Depends(get_db)):
    user = await get_user_by_id(user_id, db)
    if user is None:
        raise HTTPException(status_code=404, detail=ERROR_USER_NOT_FOUND)
    return user


@router.put("/{user_id}/", response_model=UserUpdate)
async def update_user(user_id: int, body: UserUpdate, db: Session = Depends(get_db),
                      current_user: User = Depends(auth_service.get_current_user)):
    if current_user.id == user_id:
        user = await update(user_id, body, db)
    if user is None:
        raise HTTPException(status_code=404, detail=ERROR_USER_NOT_FOUND)
    return await get_user_by_id(user_id, db)
