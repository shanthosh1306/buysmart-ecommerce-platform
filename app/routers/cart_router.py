from fastapi import APIRouter, HTTPException, Request, Depends, Form
from sqlalchemy.orm import Session
from typing import Annotated

from app.models.products import Product
from app.models.cart import Cart
from app.models.users import User
from app.database import SessionLocal
from app.auth.dependencies import get_current_user_token

from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse


router = APIRouter(prefix="/cart", tags=["Cart"])
templates = Jinja2Templates(directory="app/templates")


# -----------------------------
# DB Dependency
# -----------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[User | None, Depends(get_current_user_token)]


# -----------------------------
# ADD TO CART
# -----------------------------
@router.post("/add/{id}")
def create_cart(
    request: Request,
    db: db_dependency,
    id: int,
    USER_ID: user_dependency
):
    if not USER_ID:
        return RedirectResponse(
            url=f"/auth/login?next=/products/{id}",
            status_code=303
        )

    product = db.query(Product).filter(Product.id == id).first()
    if not product:
        return RedirectResponse(url="/", status_code=303)

    cart_item = db.query(Cart).filter(
        Cart.user_id == USER_ID.id,
        Cart.product_id == id
    ).first()

    if cart_item:
        cart_item.quantity += 1
    else:
        db.add(Cart(
            user_id=USER_ID.id,
            product_id=id,
            quantity=1
        ))

    db.commit()
    return RedirectResponse(url="/cart", status_code=303)


# -----------------------------
# VIEW CART
# -----------------------------
@router.get("/")
def view_cart(
    request: Request,
    db: db_dependency,
    USER_ID: user_dependency
):
    if not USER_ID:
        return RedirectResponse(
            url="/auth/login?next=/cart",
            status_code=303
        )

    cart_items = (
        db.query(Cart, Product)
        .join(Product, Cart.product_id == Product.id)
        .filter(Cart.user_id == USER_ID.id)
        .all()
    )

    cart_data = []
    total_price = 0

    for cart_item, product in cart_items:
        item_total = product.price * cart_item.quantity
        total_price += item_total

        cart_data.append({
            "id": product.id,
            "name": product.name,
            "price": product.price,
            "quantity": cart_item.quantity,
            "item_total": item_total
        })

    return templates.TemplateResponse(
        "cart.html",
        {
            "request": request,
            "cart": cart_data,
            "total_price": total_price,
            "user": USER_ID
        }
    )


# -----------------------------
# UPDATE CART
# -----------------------------
@router.post("/update/{product_id}")
def update_cart(
    product_id: int,
    db: db_dependency,
    USER_ID: user_dependency,
    quantity: int = Form(...)
):
    if not USER_ID:
        return RedirectResponse("/auth/login", status_code=303)

    cart_item = db.query(Cart).filter(
        Cart.user_id == USER_ID.id,
        Cart.product_id == product_id
    ).first()

    if not cart_item:
        return RedirectResponse("/cart", status_code=303)

    if quantity <= 0:
        db.delete(cart_item)
    else:
        cart_item.quantity = quantity

    db.commit()
    return RedirectResponse(url="/cart", status_code=303)


# -----------------------------
# DELETE CART ITEM
# -----------------------------
@router.post("/delete/{product_id}")
def delete_cart(
    product_id: int,
    db: db_dependency,
    USER_ID: user_dependency
):
    if not USER_ID:
        return RedirectResponse("/auth/login", status_code=303)

    cart_item = db.query(Cart).filter(
        Cart.user_id == USER_ID.id,
        Cart.product_id == product_id
    ).first()

    if cart_item:
        db.delete(cart_item)
        db.commit()

    return RedirectResponse(url="/cart", status_code=303)
