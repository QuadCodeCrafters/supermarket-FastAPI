from sqlalchemy import Boolean, column, Integer, String, Column, DOUBLE , Enum
from database import Base

class Users(Base):
      __tablename__ = 'users'

      id = Column(Integer, primary_key=True , index= True )
      username = Column(String(50) , unique=True )
      password = Column(String(500))

class Orders(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True , index= True )
    order_items = Column(String(100))
    qty = Column(Integer)
    price = Column(DOUBLE)
    status = Column(Enum("Pending", "Successful", name="order_status"),server_default="Pending",nullable=False,)
    user_id = Column(Integer, nullable=False)



class Items(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True , index= True )
    name = Column(String(100))
    description = Column(String(100))
    price = Column(DOUBLE)
    qty = Column(Integer)
    status = Column(Enum('Available', 'Unavailable', name='item_status'), default='Available')

