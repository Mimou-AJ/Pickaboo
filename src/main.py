from fastapi import FastAPI
import os
from .database.core import engine, Base
from .build_persona.entity import Persona # Import models to register them
from .questions.entity import Question, Answer # Import models to register them
from .messages.entity import MessageHistory # Import models to register them
from .api import register_routes
from .logging import configure_logging, LogLevels


configure_logging(LogLevels.info)

app = FastAPI()

# Create tables only when explicitly enabled to avoid DB connection issues during tests
if os.getenv("ENABLE_DB_INIT", "false").lower() == "true":
    Base.metadata.create_all(bind=engine)

register_routes(app)