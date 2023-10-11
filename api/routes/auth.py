from fastapi import APIRouter, HTTPException,logger, Depends, status, Security, BackgroundTasks, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from fastapi.templating import Jinja2Templates
from starlette.requests import Request
from fastapi import FastAPI, Form, Body, BackgroundTasks
import logging
from typing import Optional, Union

from api.database.db import get_db
from api.repository import users as repository_users
from api.services.auth import auth_service
from api.services.conf_email import send_email
from api.schemas import UserModel, UserResponse, TokenModel, RequestEmail, SignupForm
from api.conf.config import settings

router = APIRouter(prefix='/auth', tags=['auth'])
security = HTTPBearer()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

templates = Jinja2Templates(directory="templates")

@router.get('/signup/')
async def signup_page(request: Request):

    return templates.TemplateResponse("signup.html", {"request": request})

@router.get('/login/')
async def login_page(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})

@router.get('/logout/')
async def logout_page(request: Request):
    return templates.TemplateResponse("logout.html", {"request": request})

@router.get('/email_conformation/')
async def email_conformation_page(request: Request):
    return templates.TemplateResponse("email_conformation_page.html", {"request": request})

@router.get('/email_verified/')
async def email_verified_page(request: Request):
    return templates.TemplateResponse("email_verified.html", {"request": request})


@router.post('/signup/', response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db), username: str = Form(...), email: str = Form(...), password: str = Form(...)
                  ):
    # Перевірка користувача
    exist_user = await repository_users.get_user_by_email(email, db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail='Account already exists')

    # Хешування пароля
    hashed_password = auth_service.get_password_hash(password)

    # Створення нового об'єкта UserModel для збереження в базі даних
    user_data = UserModel(username=username, email=email, password=hashed_password)

    new_user = await repository_users.create_user(user_data, db)
    background_tasks.add_task(send_email, new_user.email, new_user.username, request.base_url)
    return  RedirectResponse(url="/api/auth/email_conformation/", status_code=303)


@router.post('/login/')
async def login(db: Session = Depends(get_db), username: str = Form(...), password: str = Form(...)):
    user = await repository_users.get_user_by_email(username, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect data')

    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Email not confirmed')

    if not auth_service.verify_password(password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Incorrect data')

    access_token = await auth_service.create_access_token(data={'sub': user.email})
    refresh_token = await auth_service.create_refresh_token(data={'sub': user.email})
    await repository_users.update_token(user, refresh_token, db)

    response = RedirectResponse(url=f"{settings.STREAMLIT_URL}?token={access_token}", status_code=303)  # Redirecting to the home page
    response.set_cookie(key="access_token", value=access_token, httponly=True)
    response.set_cookie(key="refresh_token", value=refresh_token, httponly=True)
    return response


@router.post('/logout/')
async def logout(request: Request, token: str = Depends(auth_service.oauth2_scheme), db: Session = Depends(get_db)):
    user = await repository_users.get_user_by_token(token, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    # Invalidate the refresh token in the database
    user.refresh_token = None
    db.commit()

    # Delete the cookies
    response = RedirectResponse("logout.html", status_code=303)
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")

    return response

@router.get('/refresh_token/', response_model=TokenModel)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_users.get_user_by_email(email, db)
    if user.refresh_token != token:
        await repository_users.update_token(user, None, db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid refresh token')
    access_token = await auth_service.create_access_token(data={'sub': email})
    refresh_token = await auth_service.create_refresh_token(data={'sub': email})
    await repository_users.update_token(user, refresh_token, db)
    return {'access_token': access_token, 'refresh_token': refresh_token, 'token_type': 'bearer'}


@router.get('/confirmed_email/{token}')
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    logger.info(f"Processing token: {token}")
    try:
        email = await auth_service.get_email_from_token(token)
        logger.debug(f"Decoded email from token: {email}")
    except Exception as e:
        logger.error(f"Error decoding token: {e}")
        raise

    user = await repository_users.get_user_by_email(email, db)
    if not user.confirmed:
        await repository_users.confirmed_email(email, db)
        logger.info(f"Email {email} has been confirmed")
        return RedirectResponse(url="/", status_code=303)
    else:
        logger.warning(f"Email {email} is already confirmed")

    if user is None:
        logger.warning(f"No user found for email: {email}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Verification error')
    return RedirectResponse(url="/api/auth/email_verified/")

@router.post('/request_email/')
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request, db: Session = Depends(get_db)):

    user = await repository_users.get_user_by_email(body.email, db)
    if user.confirmed:
        return {'message': 'Your email is already confirmed'}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, request.base_url)
    return {'message': 'Check your email for confirmation.'}


@router.get("/is_user_authenticated/")
def is_user_authenticated(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return False

    try:
        user = auth_service.get_current_user(token, db)
        if user:
            return True
    except HTTPException:
        return False

@router.get("/get_user_id/")
async def get_user_id(token: Optional[str] = None, db: Session = Depends(get_db)):
    if not token:
        raise HTTPException(status_code=400, detail="Token is missing")

    try:
        user = await auth_service.get_current_user(token, db)
        if user:
            return {"user_id": user.id}
    except HTTPException:
        raise HTTPException(status_code=401, detail="Invalid token or user not found")