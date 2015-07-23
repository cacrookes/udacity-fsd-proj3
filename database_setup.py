import os
import sys
from sqlalchemy import Column, ForeignKey, Integer, String, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()

# Defines categories
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
        }

# Defines attributes for an item
class Item(Base):
    __tablename__ = 'item'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    price = Column(Numeric(12,2), default=0)
    description = Column(String(250))
    num_avail = Column(Integer, default=0)
    image = Column(String(120))
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'price': self.price,
            'description': self.description,
            'num_avail': self.num_avail,
            'image': self.image,
        }


engine = create_engine('sqlite:///hockeyshop.db')
Base.metadata.create_all(engine)
