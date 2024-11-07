from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime
from sqlalchemy.orm import sessionmaker, declarative_base  # Updated import
import datetime

# Initialize database engine and session
engine = create_engine('postgresql://postgres:Admin@localhost:5432/book_database')
Session = sessionmaker(bind=engine)
session = Session()
Base = declarative_base()  # No change needed here since the import is updated

# Define Product model
class Product(Base):
    __tablename__ = 'products'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price_mdl = Column(Float, nullable=False)
    price_eur = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    link = Column(String, nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

# Create the table
Base.metadata.create_all(engine)

def get_db():
    db = Session()
    try:
        yield db
    finally:
        db.close()
