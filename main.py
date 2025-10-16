import os
import time
from typing import List
from contextlib import contextmanager

from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from pydantic import BaseModel
from faker import Faker

# --- 1. Configuration and Database Setup ---

# NOTE: REPLACE THIS WITH YOUR ACTUAL POSTGRESQL CONNECTION STRING
# Example format: "postgresql://user:password@host:port/database_name"
# Ensure the database 'fastapi_users_db' exists before running the app.
POSTGRES_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/fastapi_users_db" # 
)

# SQLAlchemy Setup
MAX_RETRIES = 5
RETRY_DELAY = 3  # seconds

def get_engine():
    """Initializes the database engine with retry logic."""
    for i in range(MAX_RETRIES):
        try:
            engine = create_engine(POSTGRES_URL, echo=False)
            # Try to connect immediately to trigger an OperationalError if needed
            with engine.connect() as connection:
                print("Database connection successful.")
            return engine
        except OperationalError as e:
            print(f"Database connection failed (Attempt {i+1}/{MAX_RETRIES}): {e}")
            if i < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise e # Re-raise if all retries fail

ENGINE = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)
Base = declarative_base()

# --- 2. SQLAlchemy Model (Database Table Structure) ---

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String, index=True)
    lastname = Column(String, index=True)
    zip_code = Column(String)
    country = Column(String)

# Create tables (only if they don't exist)
Base.metadata.create_all(bind=ENGINE)

# --- 3. Pydantic Schemas (Data Validation and Response Models) ---

class UserBase(BaseModel):
    firstname: str
    lastname: str
    zip_code: str
    country: str

class UserCreate(UserBase):
    pass # Same fields for creation

class UserSchema(UserBase):
    id: int

    class Config:
        # Enables conversion from SQLAlchemy model instances to Pydantic objects
        from_attributes = True

# --- 4. FastAPI Application Setup and Dependencies ---

app = FastAPI(
    title="PostgreSQL FastAPI CRUD API",
    description="A simple API for managing user records with CRUD operations and a data seeder.",
    version="1.0.0"
)

# Dependency to get a database session
@contextmanager
def get_db():
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_db_session():
    """Returns a database session object using the context manager."""
    try:
        with get_db() as db:
            yield db
    except SQLAlchemyError as e:
        print(f"Database error during request: {e}")
        raise HTTPException(status_code=500, detail="Database connection or query failed")

# --- 5. API Endpoints (CRUD Operations) ---

@app.post("/users/", response_model=UserSchema, status_code=201, summary="Create a new user")
def create_user(user: UserCreate, db: SessionLocal = Depends(get_db_session)):
    """
    Adds a new user record to the database.
    """
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/", response_model=List[UserSchema], summary="Read all users")
def read_users(skip: int = 0, limit: int = 100, db: SessionLocal = Depends(get_db_session)):
    """
    Retrieves a list of all user records, with optional pagination.
    """
    users = db.query(User).offset(skip).limit(limit).all()
    return users

@app.get("/users/{user_id}", response_model=UserSchema, summary="Read a single user by ID")
def read_user(user_id: int, db: SessionLocal = Depends(get_db_session)):
    """
    Retrieves a single user record based on its unique ID.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserSchema, summary="Modify an existing user")
def update_user(user_id: int, user_update: UserCreate, db: SessionLocal = Depends(get_db_session)):
    """
    Updates the data for an existing user record.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    # Update fields
    for key, value in user_update.dict().items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

@app.delete("/users/{user_id}", status_code=204, summary="Remove a user")
def delete_user(user_id: int, db: SessionLocal = Depends(get_db_session)):
    """
    Deletes a user record permanently from the database.
    """
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return

# --- 6. Data Seeder Endpoint ---

@app.post("/populate_50", status_code=201, summary="Seed the database with 50 fake users")
def populate_data(db: SessionLocal = Depends(get_db_session)):
    """
    Populates the 'users' table with 50 lines of synthetic data using the Faker library.
    """
    fake = Faker()
    new_users = []
    
    for _ in range(50):
        # Create a new User object with fake data
        new_user = User(
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            zip_code=fake.postcode(),
            country=fake.country()
        )
        new_users.append(new_user)
    
    # Add all 50 users to the session and commit
    db.add_all(new_users)
    db.commit()
    
    return {"message": f"Successfully added {len(new_users)} fake users to the database."}

# --- 7. Root Endpoint ---

@app.get("/")
def root():
    return {"message": "Welcome to the FastAPI PostgreSQL CRUD API. Go to /docs for the interactive API documentation."}
# --- End of File ---