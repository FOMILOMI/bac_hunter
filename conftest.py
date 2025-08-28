# conftest.py
import os
import pytest

# Ensure tests are not influenced by local auth_data.json
os.environ.setdefault("BH_DISABLE_AUTH_STORE", "1")

@pytest.fixture(autouse=True)
def _reset_env_for_tests(monkeypatch):
	# Provide consistent environment for each test without forcing offline mode
	monkeypatch.setenv("BH_DISABLE_AUTH_STORE", "1")
	yield
	# cleanup is automatic with monkeypatch


@pytest.fixture
def sample_responses():
	return [
		{
			'url': 'https://api.example.com/users/123',
			'status_code': 200,
			'headers': {'content-type': 'application/json'},
			'body': '{"user_id": 123, "email": "john@example.com", "name": "John Doe"}',
			'request_headers': {'Authorization': 'Bearer token123'}
		},
		{
			'url': 'https://api.example.com/users/456',
			'status_code': 200,
			'headers': {'content-type': 'application/json'},
			'body': '{"user_id": 456, "email": "jane@example.com", "name": "Jane Smith"}',
			'request_headers': {'Authorization': 'Bearer token456'}
		},
		{
			'url': 'https://api.example.com/admin/dashboard',
			'status_code': 200,
			'headers': {'content-type': 'text/html'},
			'body': '<html><body><h1>Admin Dashboard</h1><p>Welcome administrator</p></body></html>',
			'request_headers': {'Cookie': 'session=user123'}
		}
	]


# Intentionally do not define a generic session_manager fixture to avoid
# interfering with tests that provide their own specialized fixtures.
@pytest.fixture
def session_manager(tmp_path):
	from bac_hunter.session_manager import SessionManager
	sm = SessionManager()
	sm.configure(sessions_dir=str(tmp_path), enable_semi_auto_login=True)
	return sm