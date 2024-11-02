from __future__ import annotations

from pathlib import Path

import orjson
from yarl import URL

from telguarder.const import TELGUARDER_API_URL

LOOKUP_URL_PATH = URL(TELGUARDER_API_URL).path
FIXTURE_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> str:
    """Load a fixture."""
    path = FIXTURE_DIR / f"{name}.json"
    if not path.exists():  # pragma: no cover
        raise FileNotFoundError(f"Fixture {name} not found")
    return path.read_text(encoding="utf-8")


def load_fixture_json(name: str) -> dict | list:
    """Load a fixture as JSON."""
    data = load_fixture(name)
    return orjson.loads(data)
