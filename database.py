from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 1. Setup the Database URL (SQLite)
SQLALCHEMY_DATABASE_URL = "sqlite:///./scenario.db"

# 2. Create the Engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 3. Create the SessionLocal class
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 4. Create the Base class
Base = declarative_base()

# 5. Define the Booking Table
class Booking(Base):
    __tablename__ = "bookings"
    id = Column(Integer, primary_key=True, index=True)
    customer_name = Column(String)
    customer_number = Column(String)
    start_location = Column(String)
    destination = Column(String)
    time = Column(String)
    car_type = Column(String)
    status = Column(String, default="Pending")

# 6. THE MISSING FUNCTION (Add this now!)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()