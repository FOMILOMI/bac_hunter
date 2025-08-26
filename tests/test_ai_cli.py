import sys
sys.path.insert(0, '/workspace')
from bac_hunter.cli import app

def test_ai_commands_registered():
	callbacks = {getattr(c, 'callback', None) for c in app.registered_commands}
	names = {getattr(cb, '__name__', '') for cb in callbacks}
	assert 'ai_predict' in names
	assert 'ai_zeroday' in names
	assert 'ai_evasion' in names
	assert 'ai_brief' in names