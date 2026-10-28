from uuid import uuid4

import pytest


@pytest.fixture
def session_headers():
    return {"X-Course-Session": f"autotest-{uuid4()}"}


@pytest.fixture
def session_headers_pair():
    return [{"X-Course-Session": f"autotest-{uuid4()}"} for _ in range(2)]
