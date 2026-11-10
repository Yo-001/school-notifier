import sys
import json
from pathlib import Path
from unittest.mock import patch

import importlib.util

# Load the monitor module from its path
PROJECT_DIR = Path(__file__).parent.parent
spec = importlib.util.spec_from_file_location('monitor', PROJECT_DIR / 'monitor.py')
monitor = importlib.util.module_from_spec(spec)
spec.loader.exec_module(monitor)

FIXTURE_DIR = PROJECT_DIR / 'tests' / 'fixtures'


def load_fixture(name):
    return (FIXTURE_DIR / name).read_text(encoding='utf-8')


def test_rss_parsing():
    rss = load_fixture('sample.rss')
    items = monitor.parse_rss(rss)
    assert len(items) == 1
    item = items[0]
    assert item['id'] == 500
    assert item['title'] == 'Nota de exemplo'
    assert item['link'].endswith('/node/500')
    assert '2024' in item['date']
    assert item['summary'] == 'Resumo da nota.'


def run_main_with_mock(monkeypatch, seen_ids, expect_email):
    # Prepare temporary state directory
    tmp_state = PROJECT_DIR / 'state_test'
    tmp_state.mkdir(exist_ok=True)
    seen_path = tmp_state / 'seen.json'
    seen_path.write_text(json.dumps({'ids': list(seen_ids)}), encoding='utf-8')
    # Patch paths used by monitor
    monkeypatch.setattr(monitor, 'STATE_DIR', tmp_state)
    monkeypatch.setattr(monitor, 'SEEN_PATH', seen_path)
    # Mock fetch_url to return RSS fixture
    monkeypatch.setattr(monitor, 'fetch_url', lambda url, ua, timeout=20: load_fixture('sample.rss'))
    # Capture email calls
    sent = []
    def fake_send_email(new_items, dry_run=False):
        sent.append((new_items, dry_run))
    monkeypatch.setattr(monitor, 'send_email', fake_send_email)
    # Simulate command-line args
    monkeypatch.setattr(sys, 'argv', ['monitor.py', '--dry-run'])
    # Run
    monitor.main()
    if expect_email:
        assert len(sent) == 1
        assert any(item['id'] == 500 for item in sent[0][0])
    else:
        assert len(sent) == 0


def test_first_run_no_email(monkeypatch):
    # No previous ids -> baseline, should not send email
    run_main_with_mock(monkeypatch, seen_ids=set(), expect_email=False)


def test_second_run_sends_email(monkeypatch):
    # Previous run saw id 470 only, new id 500 appears -> email should be sent
    run_main_with_mock(monkeypatch, seen_ids={470}, expect_email=True)


def test_failure_sends_alert_email(monkeypatch):
    # When fetch_url raises, an alert email should be sent immediately (1 fail)
    tmp_state = PROJECT_DIR / 'state_test'
    tmp_state.mkdir(exist_ok=True)
    seen_path = tmp_state / 'seen.json'
    seen_path.write_text(json.dumps({'ids': []}), encoding='utf-8')
    monkeypatch.setattr(monitor, 'STATE_DIR', tmp_state)
    monkeypatch.setattr(monitor, 'SEEN_PATH', seen_path)
    def boom(url, ua, timeout=20):
        raise IOError('boom')
    monkeypatch.setattr(monitor, 'fetch_url', boom)
    sent = []
    def fake_send_email(new_items, dry_run=False):
        sent.append((new_items, dry_run))
    monkeypatch.setattr(monitor, 'send_email', fake_send_email)
    monkeypatch.setattr(sys, 'argv', ['monitor.py', '--dry-run'])
    with patch.object(sys, 'exit', side_effect=SystemExit) as mock_exit:
        try:
            monitor.main()
        except SystemExit:
            pass
    assert len(sent) == 1
    assert 'Falha' in sent[0][0][0]['title']
    mock_exit.assert_called_once_with(1)