import os
import sys
import datetime
from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

#----------------------------------------------------------------------
# This app defines a database for a catalog app. App supports different
# categories, with items belonging to different categories.
#----------------------------------------------------------------------

Base = declarative_base()

# Defines categories
class Category(Base):
    __tablename__ = 'category'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), unique=True)

    # serialize table to make data json friendly
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
    # price will be stored in cents with the app handling converting to dollars.
    # This allow us to use Integer type. Decimal is not being used due to compiler
    # warnings about lack of native Decimal support. This also makes the database
    # more flexible for different currencies.
    price = Column(Integer, default=0)
    description = Column(String(250), default="")
    num_avail = Column(Integer, default=0)
    image = Column(String(120), default="")
    date_added = Column(DateTime, default=datetime.datetime.utcnow)
    category_id = Column(Integer, ForeignKey('category.id'))
    category = relationship(Category)

    # serialize table to make data json friendly
    @property
    def serialize(self):
        return {
            'id': self.id,
            'name': self.name,
            'price_cents': self.price,
            'description': self.description,
            'num_avail': self.num_avail,
            'image': self.image,
            'date_added': self.date_added,
        }


engine = create_engine('sqlite:///hockeyshop.db')
Base.metadata.create_all(engine)
