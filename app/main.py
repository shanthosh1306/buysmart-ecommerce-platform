from fastapi import FastAPI , status, APIRouter, Request
from app.database import engine
from sqlalchemy import text
# All ORM models must inherit from the SAME Base object.
from app.models import Base
from app.routers.admin_router import router as admin_router 
from app.routers.auth_router import router as auth_router
from app.routers.user_router import router as user_router
from app.routers.product_router import router as product_router
from app.routers.cart_router import router as cart_router
from app.routers.order_router import router as order_router
from app.routers.admin_product_router import router as admin_product_router
from app.routers.admin_order_router import router as admin_order_router
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI(title="ecommerce")

templates = Jinja2Templates(directory = "app/templates")

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return RedirectResponse(url="/products/")


app.mount("/static",StaticFiles(directory="app/static"), name="static")




'''

@app.get("/",status_code=status.HTTP_200_OK)
def test_api():
    return {"status":"ok"}

@app.get("/db-test")
def db_test():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1"))
        return {"db_status": "connected", "result": result.scalar()}

        
'''


    
app.include_router(auth_router)
app.include_router(product_router)   # 🔥 MOVE THIS UP
app.include_router(cart_router)
app.include_router(order_router)
app.include_router(user_router)
app.include_router(admin_router)
app.include_router(admin_product_router)
app.include_router(admin_order_router)
