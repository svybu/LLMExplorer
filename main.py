import uvicorn
from fastapi import FastAPI,Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.middleware.cors import CORSMiddleware
from typing import List
import logging

from api.routes.auth import is_user_authenticated
from api.routes import auth, healthcheck, user
from api.conf.config import settings

app = FastAPI(title="LLMExplorer")
logging.basicConfig(level=logging.INFO)

templates = Jinja2Templates(directory="templates")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app.include_router(healthcheck.route)
app.include_router(auth.router, prefix="/api")
app.include_router(user.router)
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def read_root(request: Request):
    user_authenticated = is_user_authenticated(request)
    return templates.TemplateResponse("index.html", {"request": request, "settings": settings
        , "user_authenticated": user_authenticated})

