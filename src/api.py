from fastapi import FastAPI
from src.auth.controller import router as auth_router
from src.users.controller import router as users_router
from src.build_persona.controller import router as build_persona_router
from src.questions.controller import router as questions_router
from src.recommendations.controller import router as recommendations_router

def register_routes(app: FastAPI):
    app.include_router(auth_router)
    app.include_router(users_router)
    app.include_router(build_persona_router)
    app.include_router(questions_router)
    app.include_router(recommendations_router)