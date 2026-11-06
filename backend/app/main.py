"""
backend/app/main.py
Main FastAPI application entrypoint for ClauseLens.
"""

from __future__ import annotations
import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

load_dotenv()

from backend.app.api.router import router as api_router
from backend.app.db.session import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize SQLite tables
    init_db()
    yield


app = FastAPI(
    title="ClauseLens API",
    description="Professional Indian Residential Tenancy Compliance & Logic Verification Engine",
    version="1.0.0",
    lifespan=lifespan
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API Router
app.include_router(api_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc), "error": "InternalServerError"}
    )


@app.get("/")
def root():
    return {
        "product": "ClauseLens",
        "tagline": "AI-Powered Contract Compliance & First-Order Logic Verification",
        "docs_url": "/docs",
        "api_health": "/api/health"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)

