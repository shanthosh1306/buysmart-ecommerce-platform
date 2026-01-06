from fastapi import  FastAPI, APIRouter, HTTPException , status, Depends, Request
from app.database import SessionLocal 
from sqlalchemy.orm import Session
from app.models.products import Product
from app.models.cart import Cart
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.payments import Payment
from typing import Annotated
from fastapi.templating import Jinja2Templates
from sqlalchemy.exc import SQLAlchemyError
from app.auth.dependencies import get_current_user_token
from app.models.users import User
from fastapi.responses import RedirectResponse

router = APIRouter(prefix="/order", tags=["Orders"])

templates = Jinja2Templates(directory="app/templates")

def get_db():
    db = SessionLocal() 
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

user_dependency = Annotated[User | None, Depends(get_current_user_token)]

@router.post("/place")
def place_order(request: Request, db: db_dependency, USER_ID: user_dependency):

    if not USER_ID:
        return RedirectResponse("/auth/login?next=/cart", status_code=303)

    try:
        cart_items = (
            db.query(Cart, Product)
            .join(Product, Cart.product_id == Product.id)
            .filter(Cart.user_id == USER_ID.id)
            .all()
        )

        if not cart_items:
            return RedirectResponse("/cart", status_code=303)

        total_price = 0

        for cart_item, product in cart_items:
            if product.stock < cart_item.quantity:
                return templates.TemplateResponse(
                    "cart.html",
                    {
                        "request": request,
                        "error": f"Insufficient stock for {product.name}"
                    }
                )
            total_price += product.price * cart_item.quantity

        order = Order(user_id=USER_ID.id, total_amount=total_price)
        db.add(order)
        db.flush()

        for cart_item, product in cart_items:
            db.add(OrderItem(
                order_id=order.id,
                product_id=product.id,
                quantity=cart_item.quantity,
                price=product.price
            ))
            product.stock -= cart_item.quantity

        payment = Payment(
            order_id=order.id,
            payment_method="COD",
            transaction_id=str(USER_ID.id)
        )

        db.add(payment)
        db.query(Cart).filter(Cart.user_id == USER_ID.id).delete()

        db.commit()

        return RedirectResponse(
            f"/order/{order.id}",
            status_code=303
        )

    except SQLAlchemyError:
        db.rollback()
        return RedirectResponse("/cart", status_code=303)


@router.get("/history")
def order_history(request: Request, db: db_dependency, USER_ID: user_dependency):

    if not USER_ID:
        return RedirectResponse("/auth/login?next=/order/history", status_code=303)

    orders = (
        db.query(Order)
        .filter(Order.user_id == USER_ID.id)
        .order_by(Order.created_at.desc())
        .all()
    )

    return templates.TemplateResponse(
        "order_history.html",
        {
            "request": request,
            "orders": orders,
            "user": USER_ID
        }
    )


@router.get("/{order_id}")
def order_detail(request: Request, order_id: int, db: db_dependency, USER_ID: user_dependency):

    if not USER_ID:
        return RedirectResponse("/auth/login?next=/order/history", status_code=303)

    order = (
        db.query(Order)
        .filter(Order.id == order_id, Order.user_id == USER_ID.id)
        .first()
    )

    if not order:
        return RedirectResponse("/order/history", status_code=303)

    order_items = (
        db.query(OrderItem, Product)
        .join(Product, OrderItem.product_id == Product.id)
        .filter(OrderItem.order_id == order.id)
        .all()
    )

    return templates.TemplateResponse(
        "order_detail.html",
        {
            "request": request,
            "order": order,
            "order_items": order_items
        }
    )
