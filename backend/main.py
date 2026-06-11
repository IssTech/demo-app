import os
import re
import time
import json
from typing import List, Generator
from contextlib import contextmanager

import requests
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, Column, Integer, String, text
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from pydantic import BaseModel
from faker import Faker

APP_VERSION = "1.1.0"

# --- 1. Configuration & Database Connection ---

POSTGRES_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:password@localhost:5432/demo_app_db"
)

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
if not OLLAMA_HOST.startswith(("http://", "https://")):
    OLLAMA_HOST = f"http://{OLLAMA_HOST}"

OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
OLLAMA_EMBED_MODEL = os.environ.get("OLLAMA_EMBED_MODEL", "nomic-embed-text:latest")

MAX_RETRIES = 5
RETRY_DELAY = 3

def get_engine():
    """Initializes and returns the database engine with resilient connection retry logic."""
    for i in range(MAX_RETRIES):
        try:
            engine = create_engine(POSTGRES_URL, echo=False)
            with engine.connect() as conn:
                pass  # Validate connection on startup
            return engine
        except OperationalError as e:
            print(f"Database connection attempt {i+1}/{MAX_RETRIES} failed: {e}")
            if i < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise e

ENGINE = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=ENGINE)
Base = declarative_base()

# --- 2. Database Schema & Tables ---

class User(Base):
    """SQLAlchemy model representing a user in the system."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    firstname = Column(String, index=True)
    lastname = Column(String, index=True)
    zip_code = Column(String)
    country = Column(String)

Base.metadata.create_all(bind=ENGINE)

def init_vector_extension():
    """Creates PGVector extension and the embeddings lookup table if not exists."""
    try:
        with ENGINE.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector;"))
            conn.execute(text("""
            CREATE TABLE IF NOT EXISTS data_embeddings (
                id SERIAL PRIMARY KEY,
                record_id INT,
                sanitized_summary TEXT,
                embedding VECTOR(768)
            );
            """))
            conn.commit()
            print("PGVector extension and data_embeddings table verified successfully.")
    except Exception as e:
        print(f"Failed to initialize PGVector extension/table: {e}")

init_vector_extension()

# --- 3. Pydantic Schemas ---

class UserBase(BaseModel):
    firstname: str
    lastname: str
    zip_code: str
    country: str

class UserCreate(UserBase):
    pass

class UserSchema(UserBase):
    id: int

    class Config:
        from_attributes = True

# --- 4. FastAPI Setup & Dependency Injection ---

app = FastAPI(
    title="PostgreSQL FastAPI CRUD API", 
    description="Demo application showcasing CRUD operations and local Agentic AI integration.",
    version=APP_VERSION
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@contextmanager
def get_db():
    """Context manager for SQLAlchemy database sessions with auto-rollback on error."""
    db = SessionLocal()
    try:
        yield db
    except SQLAlchemyError as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_db_session() -> Generator:
    """FastAPI Dependency providing a managed database session."""
    try:
        with get_db() as db:
            yield db
    except SQLAlchemyError as e:
        print(f"Database session error during request lifecycle: {e}")
        raise HTTPException(status_code=500, detail="Database connection or transaction failed")

# --- 5. Vector Embedding Helpers ---

def get_embedding(text_to_embed: str) -> list:
    """Generates a text vector embedding using the configured local Ollama instance."""
    try:
        url = f"{OLLAMA_HOST}/api/embed"
        payload = {
            "model": OLLAMA_EMBED_MODEL,
            "input": text_to_embed
        }
        r = requests.post(url, json=payload, timeout=15)
        if r.status_code == 200:
            embeddings = r.json().get("embeddings", [])
            if embeddings:
                return embeddings[0]
    except Exception as e:
        print(f"Embedding generation error: {e}")
    return None

def update_user_embedding(user_id: int, firstname: str, lastname: str, country: str, zip_code: str):
    """Syncs a user's semantic metadata and vector embedding into the data_embeddings table."""
    summary_text = f"User ID: {user_id}. Name: {firstname} {lastname}. Country: {country}. Zip Code: {zip_code}."
    emb = get_embedding(summary_text)
    if emb:
        vector_str = "[" + ",".join(map(str, emb)) + "]"
        try:
            with ENGINE.connect() as conn:
                check_sql = text("SELECT id FROM data_embeddings WHERE record_id = :record_id;")
                existing = conn.execute(check_sql, {"record_id": user_id}).fetchone()
                
                if existing:
                    update_sql = text("""
                    UPDATE data_embeddings 
                    SET sanitized_summary = :summary, embedding = :emb 
                    WHERE record_id = :record_id;
                    """)
                    conn.execute(update_sql, {
                        "summary": summary_text,
                        "emb": vector_str,
                        "record_id": user_id
                    })
                else:
                    insert_sql = text("""
                    INSERT INTO data_embeddings (record_id, sanitized_summary, embedding) 
                    VALUES (:record_id, :summary, :emb);
                    """)
                    conn.execute(insert_sql, {
                        "record_id": user_id,
                        "summary": summary_text,
                        "emb": vector_str
                    })
                conn.commit()
        except Exception as e:
            print(f"Failed to sync embedding for user {user_id}: {e}")

# --- 6. API Endpoints (CRUD Operations) ---

@app.post("/users/", response_model=UserSchema, status_code=201, summary="Create a new user")
def create_user(user: UserCreate, db: Session = Depends(get_db_session)):
    """Creates a new user record and asynchronously seeds its vector embedding."""
    db_user = User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    update_user_embedding(db_user.id, db_user.firstname, db_user.lastname, db_user.country, db_user.zip_code)
    return db_user

@app.get("/users/", response_model=List[UserSchema], summary="Read all users")
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db_session)):
    """Retrieves all registered user profiles with pagination support."""
    return db.query(User).offset(skip).limit(limit).all()

@app.get("/users/{user_id}", response_model=UserSchema, summary="Read a single user by ID")
def read_user(user_id: int, db: Session = Depends(get_db_session)):
    """Retrieves a single user record by its unique database identifier."""
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.put("/users/{user_id}", response_model=UserSchema, summary="Modify an existing user")
def update_user(user_id: int, user_update: UserCreate, db: Session = Depends(get_db_session)):
    """Updates fields on an existing user record."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in user_update.dict().items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    update_user_embedding(db_user.id, db_user.firstname, db_user.lastname, db_user.country, db_user.zip_code)
    return db_user

@app.delete("/users/{user_id}", status_code=204, summary="Remove a user")
def delete_user(user_id: int, db: Session = Depends(get_db_session)):
    """Deletes a user record permanently from the database."""
    db_user = db.query(User).filter(User.id == user_id).first()
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return

@app.delete("/users/", status_code=200, summary="Delete all users")
def delete_all_users(db: Session = Depends(get_db_session)):
    """Deletes all user records and clears the data_embeddings lookup table."""
    num_deleted = db.query(User).delete()
    db.commit()

    try:
        with ENGINE.connect() as conn:
            conn.execute(text("TRUNCATE TABLE data_embeddings RESTART IDENTITY;"))
            conn.commit()
    except Exception as e:
        print(f"Failed to clear data_embeddings table: {e}")

    return {"message": f"Successfully deleted {num_deleted} users and cleared all vector embeddings."}

@app.post("/populate_50", status_code=201, summary="Seed the database with 50 fake users")
def populate_data(db: Session = Depends(get_db_session)):
    """Generates 50 mock users using Faker and populates their vector representations."""
    fake = Faker()
    new_users = []
    
    for _ in range(50):
        new_user = User(
            firstname=fake.first_name(),
            lastname=fake.last_name(),
            zip_code=fake.postcode(),
            country=fake.country()
        )
        new_users.append(new_user)
    
    db.add_all(new_users)
    db.commit()
    
    print("[PGVector] Seeding and generating embeddings for users...")
    for user in new_users:
        db.refresh(user)
        update_user_embedding(user.id, user.firstname, user.lastname, user.country, user.zip_code)
    
    return {"message": f"Successfully added {len(new_users)} fake users with embeddings."}

@app.get("/")
def root():
    """Root status endpoint."""
    return {"message": "Welcome to the FastAPI PostgreSQL CRUD API. Go to /docs for Swagger UI."}

# --- 7. Agentic AI Chatbot Configuration & Implementation ---

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

def get_available_model():
    """Dynamically resolves the active Ollama chat model, filtering out vector embedding helpers."""
    env_model = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
    try:
        r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
        if r.status_code == 200:
            models = r.json().get("models", [])
            names = [m["name"] for m in models if "embed" not in m["name"].lower()]
            if env_model in names:
                return env_model
            for name in names:
                if env_model.split(":")[0] in name:
                    return name
            if names:
                return names[0]
    except Exception:
        pass
    return env_model

def execute_sql(query: str):
    """Executes a read-only SELECT query with robust SQL-injection and stacked-statement prevention."""
    cleaned = query.strip().lower()
    
    # 1. Defense-in-depth: Block multiple stacked statements (stacked queries)
    statements = [s.strip() for s in query.split(";") if s.strip()]
    if len(statements) > 1:
        return {"error": "Stacked queries are forbidden for safety reasons."}

    # 2. Assert read-only intent
    if not cleaned.startswith("select"):
        return {"error": "Only SELECT queries are allowed for database safety."}
        
    # 3. Keyword blocklist checks to protect against mutating operations
    forbidden = ["insert", "update", "delete", "drop", "alter", "truncate", "create", "grant", "revoke"]
    for word in forbidden:
        if re.search(r'\b' + word + r'\b', cleaned):
            return {"error": f"Operation '{word}' is forbidden for safety reasons."}
            
    try:
        with ENGINE.connect() as connection:
            result = connection.execute(text(query))
            if not result.returns_rows:
                return []
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return rows
    except Exception as e:
        return {"error": str(e)}

def execute_vector_search(query: str, limit: int = 5):
    """Executes a semantic vector similarity search via PGVector, resolving profiles dynamically."""
    emb = get_embedding(query)
    if not emb:
        return {"error": "Could not generate vector embedding for query."}
    
    vector_str = "[" + ",".join(map(str, emb)) + "]"
    
    try:
        with ENGINE.connect() as connection:
            sql = """
            SELECT u.id, u.firstname, u.lastname, u.zip_code, u.country, 
                   e.sanitized_summary, (e.embedding <=> :vector) AS distance 
            FROM data_embeddings e
            JOIN users u ON e.record_id = u.id
            ORDER BY e.embedding <=> :vector 
            LIMIT :limit;
            """
            result = connection.execute(text(sql), {"vector": vector_str, "limit": limit})
            columns = result.keys()
            rows = [dict(zip(columns, row)) for row in result.fetchall()]
            return rows
    except Exception as e:
        return {"error": str(e)}

SYSTEM_INSTRUCTION = (
    "You are an expert database-querying Agentic AI assistant for the K8s Backup Demo Application.\n"
    "Your job is to help the user query and analyze the data inside our PostgreSQL database.\n"
    "The database contains a table named 'users' with the following schema:\n"
    "- 'id': integer, primary key\n"
    "- 'firstname': string (First Name)\n"
    "- 'lastname': string (Last Name)\n"
    "- 'zip_code': string (ZIP Code / Postal Code)\n"
    "- 'country': string (Country name)\n"
    "- 'embedding': vector(768) (PGVector similarity vector column)\n\n"
    "To answer user queries, you have access to two powerful tools:\n"
    "1. 'run_sql_query': Run raw SELECT SQL statements on the 'users' table. Use this for structured data lookup, aggregating counts (e.g. total users, counts by country), or distinct list stats.\n"
    "2. 'semantic_search_users': Performs a semantic fuzzy vector-similarity search inside PGVector. Use this for fuzzy name lookups (e.g. 'find John', 'is there a user named Eric'), similarity matches, or whenever direct SQL query syntax is too strict.\n\n"
    "Guidelines:\n"
    "- Choose the most appropriate tool (or combine them) depending on the user query.\n"
    "- For security, only SELECT queries are allowed. Modifying operations are strictly forbidden.\n"
    "- Present the final output in a clear, friendly, and structured format with matching flag emojis or tables where applicable."
)

@app.post("/chat", summary="Chat with Agentic AI to query PostgreSQL database using local Ollama")
def chat_agent(request: ChatRequest):
    """Agentic AI chatbot routing conversational requests into secure local tool execution pathways."""
    model_name = get_available_model()
    
    messages_to_send = [{"role": "system", "content": SYSTEM_INSTRUCTION}]
    for msg in request.messages:
        if msg.role != "system":
            messages_to_send.append({"role": msg.role, "content": msg.content})
            
    tools = [
        {
            "type": "function",
            "function": {
                "name": "run_sql_query",
                "description": "Run a read-only SQL SELECT query on the PostgreSQL database users table. Use this for exact filters, aggregate counts, or group-by stats.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The exact SQL SELECT query to run (e.g., 'SELECT count(*) FROM users;')."
                        }
                    },
                    "required": ["query"]
                }
            }
        },
        {
            "type": "function",
            "function": {
                "name": "semantic_search_users",
                "description": "Perform a semantic vector similarity search on user profiles using natural language. Use this for fuzzy name searches, finding similar people, or natural descriptions (e.g. 'find a user named Eric' or 'look for people from Ireland').",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The natural language search terms or description (e.g. 'Eric' or 'people from Ireland')."
                        },
                        "limit": {
                            "type": "integer",
                            "description": "Maximum number of records to return (defaults to 5)."
                        }
                    },
                    "required": ["query"]
                }
            }
        }
    ]
    
    try:
        payload = {
            "model": model_name,
            "messages": messages_to_send,
            "tools": tools,
            "stream": False
        }

        response = requests.post(f"{OLLAMA_HOST}/api/chat", json=payload, timeout=300.0)
        
        if response.status_code != 200:
            raise HTTPException(status_code=500, detail=f"Ollama server returned error: {response.text}")
            
        res_data = response.json()
        message = res_data.get("message", {})
        tool_calls = message.get("tool_calls", [])
        
        if tool_calls:
            messages_to_send.append(message)
            
            for tool_call in tool_calls:
                func_name = tool_call.get("function", {}).get("name")
                func_args = tool_call.get("function", {}).get("arguments", {})
                
                if isinstance(func_args, str):
                    try:
                        func_args = json.loads(func_args)
                    except Exception:
                        pass
                
                if func_name == "run_sql_query":
                    sql_query = func_args.get("query")
                    print(f"[Agentic AI] Running tool 'run_sql_query' with SQL: {sql_query}")
                    query_result = execute_sql(sql_query)
                    print(f"[Agentic AI] Tool execution result: {query_result}")
                    
                    messages_to_send.append({
                        "role": "tool",
                        "content": json.dumps(query_result),
                        "name": "run_sql_query"
                    })
                elif func_name == "semantic_search_users":
                    search_query = func_args.get("query")
                    limit_val = func_args.get("limit", 5)
                    print(f"[Agentic AI] Running tool 'semantic_search_users' with query: {search_query}")
                    query_result = execute_vector_search(search_query, limit_val)
                    print(f"[Agentic AI] Tool execution result: {query_result}")
                    
                    messages_to_send.append({
                        "role": "tool",
                        "content": json.dumps(query_result),
                        "name": "semantic_search_users"
                    })
            
            final_payload = {
                "model": model_name,
                "messages": messages_to_send,
                "stream": False
            }
            final_response = requests.post(f"{OLLAMA_HOST}/api/chat", json=final_payload, timeout=300.0)
            
            if final_response.status_code == 200:
                final_content = final_response.json().get("message", {}).get("content", "")
                return {"response": final_content}
            else:
                return {"response": f"Error formatting the final answer: {final_response.text}"}
        else:
            return {"response": message.get("content", "I was unable to formulate an answer.")}
            
    except requests.exceptions.RequestException as re_err:
        print(f"Ollama connection error: {re_err}")
        return {"response": "Sorry, I had trouble connecting to the local Ollama LLM. Please make sure the Ollama container is running and healthy on port 11434."}
    except Exception as e:
        print(f"Chat agent general error: {e}")
        return {"response": f"An error occurred while processing the chat: {str(e)}"}
