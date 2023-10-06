import uvicorn
from fastapi import FastAPI,Request, UploadFile, File
from fastapi.templating import Jinja2Templates
from starlette.middleware.cors import CORSMiddleware
from typing import List
import logging


from api.routes import auth, healthcheck, user

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

app.include_router(healthcheck.route)
app.include_router(auth.router)
app.include_router(user.router)

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request, "title": "FastAPI with Jinja2", "message": "Hello, World!"})

