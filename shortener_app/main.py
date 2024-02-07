import validators
from typing import NoReturn
from fastapi import (
    FastAPI,
    Depends,
    Request,
    HTTPException,
)
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from . import schemas, models, crud
from .database import SessionLocal, engine


app = FastAPI()
models.Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def raise_bad_request(message: str) -> NoReturn:
    raise HTTPException(status_code=400, detail=message)


def raise_not_found(request: Request) -> NoReturn:
    message = f"URL '{request.url}' doesn't exist"
    raise HTTPException(status_code=404, detail=message)


@app.get('/')
def read_root():
    return 'Welcome to the URL shortener API'


@app.get('/{url_key}')
def forward_to_target_url(
        url_key: str,
        request: Request,
        db: Session = Depends(get_db),
    ):
    if db_url := crud.get_db_url_by_key(db=db, url_key=url_key):
        return RedirectResponse(db_url.target_url)
    return raise_not_found(request)


@app.post('/url', response_model=schemas.URLInfo)
def create_url(
        url: schemas.URLBase,
        db: Session = Depends(get_db)
    ):
    if not validators.url(url.target_url):
        raise_bad_request(message="Your provided URL is not valid")

    db_url: models.URL = crud.create_db_url(db=db, url=url)
    db_url.url = db_url.key
    db_url.admin_url = db_url.secret_key
    
    return db_url


@app.get(
    '/admin/{secret_key}',
    name='administration info',
    response_model=schemas.URLInfo,
)
def get_url_info(
        secret_key: str,
        request: Request,
        db: Session = Depends(get_db),
    ):
    if db_url := crud.get_db_url_by_secret_key(db=db, secret_key=secret_key):
        db_url.url = db_url.key
        db_url.admin_url = db_url.secret_key
        return db_url
    raise_not_found(request)
