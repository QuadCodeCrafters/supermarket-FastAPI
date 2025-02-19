import time

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database import engine, SessionLocal, Base
from passlib.context import CryptContext
from typing import Annotated
from typing import List
import models
import schemas
import requests

# Initialize FastAPI
app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Password hashing need to have because if we send the passwords through URL's it can be safe in the browser
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

# Create Tables in the Database
Base.metadata.create_all(bind=engine)

# Dependency to Get DB Session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]

#  User Register
@app.post("/UserRegister/", status_code=status.HTTP_201_CREATED)
async def create_user(user: schemas.UsersBase, db: db_dependency):
    hashed_password = pwd_context.hash(user.password)  # Hash password
    db_user = models.Users(username=user.username, password=hashed_password)  # Store hashed password
    db.add(db_user)
    db.commit()
    return {"message": "User created successfully"}

# add an item
@app.post("/AddItem/", status_code=status.HTTP_201_CREATED)
async def add_item(item: schemas.ItemsBase,db: db_dependency):
    db_item = models.Items(**item.dict())
    db.add(db_item)
    db.commit()
    return {"message": "Item added successfully"}

# user login
@app.post("/Userlogin", status_code=status.HTTP_200_OK)
async def user_login(request: schemas.UsersBase, db: Session = Depends(get_db)):
    user = db.query(models.Users).filter(models.Users.username == request.username).first()

    if user is None or not verify_password(request.password, user.password):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Incorrect username or password")

    return {"message": "Login successful", "User": request.username}

#Getall Items
@app.get("/GetAllItems/" , response_model=List[schemas.ItemsBase] , status_code=status.HTTP_200_OK)
async def get_items(db:db_dependency):
    items = db.query(models.Items).all()
    if not items:
        raise HTTPException(status_code=404, detail='No items found')
    return items

#To search an item
@app.get("/GetItem/{item_name}" , status_code = status.HTTP_200_OK)
async def get_item_by_Name(item_name: str, db: db_dependency):
    item = db.query(models.Items).filter(models.Items.name ==item_name).first()
    if item is None:
        raise HTTPException(status_code=404 , detail='Item not found')
    return item


# ESP32 URL
ESP32_URL = "http://192.168.43.153"

# Place an order
@app.post("/PlaceOrder/", status_code=status.HTTP_201_CREATED)
async def place_order(order: schemas.OrdersBase, db: db_dependency):
    user = db.query(models.Users).filter(models.Users.id == order.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    item = db.query(models.Items).filter(models.Items.name == order.order_items).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.qty < order.qty:
        raise HTTPException(status_code=400, detail="Not enough stock available")

    new_order = models.Orders(
        order_items=order.order_items,
        qty=order.qty,
        price=order.price,
        status="Pending",
        user_id=order.user_id
    )

    db.add(new_order)
    item.qty -= order.qty
    db.commit()
    db.refresh(new_order)

    # Send order details to ESP32
    try:
        response = requests.post(f"{ESP32_URL}/receive_order", json={
            "order_id": new_order.id,
            "item": order.order_items,
            "qty": order.qty,
            "price": order.price
        })
        response.raise_for_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to send order to ESP32: {str(e)}")

    # Wait for ESP32 confirmation (polling example)
    for _ in range(10):  # Try for 10 seconds
        time.sleep(1)
        order_status = db.query(models.Orders).filter(models.Orders.id == new_order.id).first()
        if order_status.status == "Successful":
            return {"message": "Order placed successfully", "order_id": new_order.id}

    raise HTTPException(status_code=500, detail="ESP32 did not confirm the order in time")

# ESP32 endpoint to update order status
@app.post("/update_order_status/")
async def update_order_status(order_id: int, status: str, db: db_dependency):
    order = db.query(models.Orders).filter(models.Orders.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = status
    db.commit()
    return {"message": f"Order status updated to {status}"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="192.168.43.126", port=8000)

