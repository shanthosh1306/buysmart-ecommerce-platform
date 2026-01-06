from fastapi import FastAPI, APIRouter, status,HTTPException ,Request ,Depends
from sqlalchemy.orm import Session
from app.models.products import Product 
from app.database import SessionLocal
from typing import Annotated

from fastapi.templating import Jinja2Templates 



router = APIRouter(prefix="/products", tags=["Products"])

templates = Jinja2Templates(directory="app/templates")  


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

@router.get("/", include_in_schema=True)
def home_product(request: Request, db: db_dependency):
    products = db.query(Product).all()

    if not products:
        raise HTTPException(status_code=404, detail="No products found")

    return templates.TemplateResponse(
        "home.html",
        {"request": request, "products": products}
    )


@router.get("/{id}")
def get_product(request: Request, id: int, db: db_dependency):
    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return templates.TemplateResponse(
        "product_detail.html",
        {"request": request, "show_product": product}
    )