from pydantic import BaseModel

# Pydantic Schema for Users
class UsersBase(BaseModel):
    username: str
    password: str

# Pydantic Schema for Orders
class OrdersBase(BaseModel):
    order_items: str
    qty: int
    price: float
    status: str
    user_id: int

# Pydantic Schema for Items
class ItemsBase(BaseModel):
    name: str
    description: str
    price :float
    qty: int
    status: str
