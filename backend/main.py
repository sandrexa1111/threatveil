import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import app as chat_app


def create_app() -> FastAPI:
    application = FastAPI(title="ThreatVeil API", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("CORS_ORIGINS", "http://localhost:3000")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Mount chat sub-app under root (keeps simple structure for MVP)
    application.mount("/", chat_app)
    return application


app = create_app()



