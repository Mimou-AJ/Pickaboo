from fastapi import FastAPI
from .database.core import engine, Base
from .entities.user import User  # Import models to register them
from .build_persona.entity import Persona # Import models to register them
from .questions.entity import Question, Answer # Import models to register them
from .api import register_routes
from .logging import configure_logging, LogLevels


configure_logging(LogLevels.info)

app = FastAPI()

""" Only uncomment below to create new tables, 
otherwise the tests will fail if not connected
"""
Base.metadata.create_all(bind=engine)

register_routes(app)