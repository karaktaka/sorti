import pytest
from typing import Dict
from unittest.mock import MagicMock

@pytest.fixture
def mock_imap():
    """Create a mock IMAP connection"""
    mock = MagicMock()
    # Mock successful login
    mock.login.return_value = ('OK', [b'Logged in'])
    # Mock folder list
    mock.list.return_value = ('OK', [
        b'(\\HasNoChildren) "/" "INBOX"',
        b'(\\HasNoChildren) "/" "Spam"',
        b'(\\HasNoChildren) "/" "Archive"'
    ])
    return mock

@pytest.fixture
def mock_email_message():
    """Create a mock email message"""
    mock = MagicMock()
    mock.get_content_type.return_value = "text/plain"
    mock.get_payload.return_value = "Test email content"
    return mock

@pytest.fixture
def config() -> Dict:
    """Sample configuration for testing"""
    return {
        'email': 'test@example.com',
        'password': 'secret',
        'server': 'imap.example.com',
        'port': 993,
        'keywords': ['invoice', 'rechnung'],
        'tag_name': 'paperless',
        'excluded_folders': ['Spam', 'Trash']
    }
