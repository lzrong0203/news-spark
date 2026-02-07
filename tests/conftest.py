"""Root test configuration."""


def pytest_collection_modifyitems(items):
    """Reorder tests: unit tests first, then e2e.

    Playwright's sync API leaves an event loop running that conflicts
    with pytest-asyncio's Runner. Running unit (async) tests before
    e2e (sync/Playwright) tests avoids this clash.
    """
    unit_tests = [t for t in items if "/unit/" in str(t.fspath)]
    e2e_tests = [t for t in items if "/e2e/" in str(t.fspath)]
    other_tests = [t for t in items if t not in unit_tests and t not in e2e_tests]
    items[:] = unit_tests + other_tests + e2e_tests
