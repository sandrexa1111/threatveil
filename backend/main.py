import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.chat import router as chat_router
from api.vendors import router as vendors_router


def create_app() -> FastAPI:
    application = FastAPI(title="ThreatVeil API", version="0.1.0")
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[os.getenv("CORS_ORIGINS", "http://localhost:3000")],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(chat_router)
    application.include_router(vendors_router)
    return application


app = create_app()



