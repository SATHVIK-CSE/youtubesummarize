"""Cloudflare Python Workers entrypoint for the FastAPI app."""
from workers import asgi
from server import app

Default = asgi.entrypoint(app)
