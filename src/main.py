from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
from sqlalchemy import text
from .database.core import engine, Base
from .build_persona.entity import Persona # Import models to register them
from .questions.entity import Question, Answer # Import models to register them
from .messages.entity import MessageHistory # Import models to register them
from .products.entity import Product # Import models to register them
from .api import register_routes
from .logging import configure_logging, LogLevels


configure_logging(LogLevels.info)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create tables only when explicitly enabled to avoid DB connection issues during tests
if os.getenv("ENABLE_DB_INIT", "false").lower() == "true":
    with engine.begin() as connection:
        connection.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
    Base.metadata.create_all(bind=engine)

register_routes(app)