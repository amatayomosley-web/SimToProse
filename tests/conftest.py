"""conftest.py — pytest fixtures for the test suite.

The engine tests (test_ledger.py, test_vault.py) are script-style: each test
takes a positional `tmp` temp-dir path and their `__main__` block passes one
`tempfile.mkdtemp()` to every test. Run as `python tests/test_ledger.py` they
pass; under pytest the `tmp` parameter is read as a fixture request, so without
this fixture pytest errors with "fixture 'tmp' not found" at collection.

This fixture makes both runners work: it yields a fresh temp-dir path string
(function-scoped, so each test gets isolated storage) and cleans it up after.
Semantics match the `__main__` harness — a path string the test joins db names
onto — while giving stronger per-test isolation than the shared-dir runner.

Stdlib only, consistent with the repo's no-third-party-in-engine discipline
(pytest is a dev/test dependency, not imported by src/engine).
"""
import shutil
import tempfile

import pytest


@pytest.fixture
def tmp():
    """Fresh temp directory (path string) per test; removed on teardown."""
    path = tempfile.mkdtemp(prefix="swe_pytest_")
    try:
        yield path
    finally:
        shutil.rmtree(path, ignore_errors=True)
