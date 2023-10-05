import uvicorn
from fastapi import FastAPI, Path, Query, Request, Depends
from fastapi import FastAPI
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from starlette.requests import Request, FileResponse
from fastapi.responses import HTMLResponse


from starlette.middleware.cors import CORSMiddleware

from api.routes import auth, healthcheck, user

app = FastAPI(title="LLMExplorer")

app.mount("/static", StaticFiles(directory="static"), name="static")

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

@app.get("/api/healthchecker")
def root():
    return {"message": "Welcome to FastAPI!"}


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse('index.html', {'request': request})
#return templates.TemplateResponse("index.html", )

@app.get("/form_post", response_class=HTMLResponse)
async def form_post(request: Request):
    return templates.TemplateResponse('form_post.html', {'request': request})


@app.get("/signup", response_class=HTMLResponse)
async def signup(request: Request):
    return templates.TemplateResponse('signup.html', {'request': request})


@app.get("/login", response_class=HTMLResponse)
async def login(request: Request):
    return templates.TemplateResponse('login.html', {'request': request})


@app.get("/logout", response_class=HTMLResponse)
async def logout(request: Request):
    return templates.TemplateResponse('logout.html', {'request': request})


if __name__ == "__main__":
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)
