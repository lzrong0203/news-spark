"""E2E test fixtures - Streamlit server management."""

import subprocess
import time

import httpx
import pytest


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Override default browser context args for E2E tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1280, "height": 900},
    }

STREAMLIT_PORT = 8502
STREAMLIT_BASE_URL = f"http://127.0.0.1:{STREAMLIT_PORT}/news-spark"


def _wait_for_server(url: str, timeout: float = 30.0) -> None:
    """Poll until the Streamlit server responds with 200."""
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            resp = httpx.get(url, follow_redirects=True, timeout=5.0)
            if resp.status_code == 200:
                return
        except httpx.ConnectError:
            pass
        time.sleep(0.5)
    msg = f"Streamlit server did not start within {timeout}s"
    raise TimeoutError(msg)


@pytest.fixture(scope="session")
def streamlit_server():
    """Start a Streamlit server for E2E testing and tear it down after."""
    proc = subprocess.Popen(
        [
            "uv",
            "run",
            "streamlit",
            "run",
            "app/main.py",
            "--server.port",
            str(STREAMLIT_PORT),
            "--server.headless",
            "true",
            "--server.baseUrlPath",
            "news-spark",
            "--browser.gatherUsageStats",
            "false",
        ],
        cwd="/home/lzrong/Projects/AI_News",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    _wait_for_server(STREAMLIT_BASE_URL)
    yield STREAMLIT_BASE_URL
    proc.terminate()
    proc.wait(timeout=10)


@pytest.fixture()
def app_url(streamlit_server):
    """Return the running Streamlit app URL."""
    return streamlit_server
