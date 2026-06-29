from pathlib import Path

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
SCREENSHOT_FIXTURE = FIXTURES_DIR / "brazil_japan_screenshot.jpg"


@pytest.fixture(scope="session")
def screenshot_bytes() -> bytes:
    assert SCREENSHOT_FIXTURE.is_file(), f"Missing fixture: {SCREENSHOT_FIXTURE}"
    data = SCREENSHOT_FIXTURE.read_bytes()
    assert len(data) > 10_000, "Screenshot fixture looks too small"
    return data
