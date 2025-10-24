from database import Base
from sqlalchemy import Column, Integer, String


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String)
    hashed_password = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    email = Column(String)
    role = Column(String)
    embedding = Column(String)
