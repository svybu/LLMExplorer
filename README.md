# LLMExplorer

REST API for exploring Large Language Models (LLMs).

This project is fueled by the FastAPI web-framework, boasting a straightforward web-interface for user interaction alongside robust REST API support. The data is managed in a Postgres database.

## REST API features:  
- User registration, authentication, and authorization;
- Confirmation email dispatch upon new user registration;

## Web interface features:  
(Add relevant features here)

## Technology stack:
 
- Python;
- FastAPI web-framework;
- Docker, Docker Hub;
- Pycharm IDE;
- Sphinx documentation builder;
- Postgres database engine;

## Steps to run the application without containerization
1. Clone the repository and navigate to its root directory:  
`git clone git@github.com:svybu/llmexplorer.git`  
`cd llmexplorer`
2. Create virtual environment and activate it:  
with `poetry`:  
`poetry shell`  

3. Install packages:  
`poetry update`  

4. Copy file `env_sample` to `.env` and change values to fit your needs  
5. You should have PosgreSQL database engine running. 
As a good example we recomment to run `postgres` in `docker` container.
For that purpose the repository has its `docker-compose.yaml` file.
Just run a command:  
`docker-compose up -d`  
...
6. Generate a new migration file if you have made changes to your models:  
   `alembic revision --autogenerate -m "Your message about the migration"`
7. Apply migrations:  
   `alembic upgrade head`

8. Start the app by typing:
`uvicorn main:app`
9. Browse the app on `http://127.0.0.1:8000`
