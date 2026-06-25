from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from strawberry.fastapi import GraphQLRouter

from .schema import schema

app = FastAPI(title="Customer Support AI Agent Demo")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

graphql_app = GraphQLRouter(schema)
app.include_router(graphql_app, prefix="/graphql")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
