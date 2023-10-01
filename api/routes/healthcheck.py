from fastapi import Depends, HTTPException, APIRouter
from sqlalchemy import text
from sqlalchemy.orm import Session

from api.database.db import get_db

route = APIRouter(tags=["healthcheck"])


@route.get("/api/healthchecker")
def healthchecker(db: Session = Depends(get_db)):
    try:
        result = db.execute(text("SELECT 1")).fetchone()
        if result is None:
            raise HTTPException(status_code=500, detail="Database is not configured correctly")
        return {"message": "Welcome to LLMExplorer API!"}
    except Exception as e:
        print(e)
        raise HTTPException(status_code=500, detail="Error connecting to the database")


@route.get("/api/", include_in_schema=False)
def root():
    return {"message": "Welcome to LLMExplorer API!"}
