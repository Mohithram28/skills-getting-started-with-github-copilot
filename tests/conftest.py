import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Fixture for FastAPI TestClient"""
    return TestClient(app)
