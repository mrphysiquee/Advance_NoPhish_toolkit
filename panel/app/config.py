import os
import secrets


class Config:
    # SECRET_KEY must be consistent across workers - generate once and cache
    SECRET_KEY = os.environ.get("SECRET_KEY", "nophish-default-secret-change-in-production")
    # Use /app/output inside Docker, fallback to local path for dev
    _output_dir = os.environ.get("OUTPUT_DIR", "/app/output")
    if not os.path.isdir(_output_dir):
        _output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "output")
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{os.path.join(_output_dir, 'panel.db')}"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DOCKER_SOCKET = "unix:///var/run/docker.sock"
    OUTPUT_DIR = _output_dir
    ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "angler")
    ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "angler")
    COLLECTION_INTERVAL = 60  # seconds
    # Project root for accessing setup files (vnc/, proxy/, etc.)
    PROJECT_ROOT = os.environ.get("PROJECT_ROOT", "/app")
