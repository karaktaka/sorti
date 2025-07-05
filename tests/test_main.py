import pytest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from sorti.main import (
    load_config,
    is_important_document,
    should_process_folder,
    get_all_folders,
    process_emails,
    parse_time_string,
    get_search_criteria
)

def test_is_important_document():
    """Test document importance detection"""
    keywords = ['rechnung', 'invoice']

    # Test subject matches
    assert is_important_document('Eine Rechnung', 'Simple content', keywords)
    assert is_important_document('Your Invoice', 'Simple content', keywords)

    # Test body matches
    assert is_important_document('Hello', 'Here is your Rechnung', keywords)
    assert is_important_document('Hello', 'Please find the invoice attached', keywords)

    # Test no matches
    assert not is_important_document('Hello', 'General message', keywords)

def test_should_process_folder():
    """Test folder exclusion logic"""
    excluded = ['Spam', 'Trash', 'Archive']

    # Test excluded folders
    assert not should_process_folder('Spam', excluded)
    assert not should_process_folder('SPAM', excluded)
    assert not should_process_folder('Trash', excluded)
    assert not should_process_folder('Archive', excluded)

    # Test included folders
    assert should_process_folder('INBOX', excluded)
    assert should_process_folder('Important', excluded)

def test_get_all_folders(mock_imap):
    """Test folder retrieval"""
    folders = get_all_folders(mock_imap)

    assert isinstance(folders, list)
    assert 'INBOX' in folders
    assert 'Spam' in folders
    assert 'Archive' in folders

@pytest.mark.parametrize('config_file_exists', [True, False])
def test_load_config(tmp_path, config_file_exists):
    """Test configuration loading with and without config file"""
    config_file = tmp_path / 'config.yaml'
    if config_file_exists:
        config_file.write_text("""
email: test@example.com
password: testpass
server: imap.example.com
keywords:
  - test
  - invoice
""")

    args = MagicMock()
    args.config = str(config_file)
    args.email = None
    args.password = None
    args.server = None
    args.port = None
    args.keywords = None
    args.tag = None
    args.exclude = None

    if config_file_exists:
        config = load_config(args)
        assert config['email'] == 'test@example.com'
        assert config['password'] == 'testpass'
        assert config['server'] == 'imap.example.com'
        assert 'test' in config['keywords']
        assert 'invoice' in config['keywords']
    else:
        with pytest.raises(ValueError):
            load_config(args)

@pytest.fixture
def mock_imap_class():
    with patch('imaplib.IMAP4_SSL') as mock:
        yield mock

def test_process_emails(mock_imap_class, mock_imap, config):
    """Test email processing"""
    mock_imap_class.return_value = mock_imap

    # Mock email search results
    mock_imap.search.return_value = ('OK', [b'1 2 3'])

    # Create a real email message for testing
    email_content = b"""From: sender@example.com
Subject: Test Invoice
Content-Type: text/plain

This is a test invoice email."""

    # Mock email fetch results with proper email content
    mock_imap.fetch.return_value = ('OK', [(b'1', email_content)])

    # Process emails
    process_emails(mock_imap, 'INBOX', config)

    # Verify interactions
    mock_imap.select.assert_called_once_with('INBOX')
    mock_imap.search.assert_called_once()
    mock_imap.fetch.assert_called()
    assert mock_imap.store.called  # Should be called because subject contains 'invoice'

def test_process_emails_with_attachment(mock_imap_class, mock_imap, config):
    """Test email processing with attachment"""
    mock_imap_class.return_value = mock_imap

    # Mock email search results
    mock_imap.search.return_value = ('OK', [b'1'])

    # Create a multipart email message for testing
    email_content = b"""From: sender@example.com
Subject: Document with Attachment
Content-Type: multipart/mixed; boundary="000000000000a"

--000000000000a
Content-Type: text/plain; charset="UTF-8"

Email with attachment

--000000000000a
Content-Type: application/pdf
Content-Disposition: attachment; filename="document.pdf"

PDF content here
--000000000000a--"""

    # Mock email fetch results
    mock_imap.fetch.return_value = ('OK', [(b'1', email_content)])

    # Process emails
    process_emails(mock_imap, 'INBOX', config)

    # Verify interactions
    mock_imap.select.assert_called_once_with('INBOX')
    mock_imap.search.assert_called_once()
    mock_imap.fetch.assert_called()
    mock_imap.store.assert_called_once()  # Should be called because of PDF attachment

def test_process_emails_no_matches(mock_imap_class, mock_imap, config):
    """Test email processing with no matching content"""
    mock_imap_class.return_value = mock_imap

    # Mock email search results
    mock_imap.search.return_value = ('OK', [b'1'])

    # Create a regular email without keywords or attachments
    email_content = b"""From: sender@example.com
Subject: Regular Email
Content-Type: text/plain

This is a regular email without any special content."""

    # Mock email fetch results
    mock_imap.fetch.return_value = ('OK', [(b'1', email_content)])

    # Process emails
    process_emails(mock_imap, 'INBOX', config)

    # Verify interactions
    mock_imap.select.assert_called_once_with('INBOX')
    mock_imap.search.assert_called_once()
    mock_imap.fetch.assert_called()
    assert not mock_imap.store.called  # Should not be called as there are no matches

def test_parse_time_string():
    """Test time string parsing"""
    assert parse_time_string('5m') == timedelta(minutes=5)
    assert parse_time_string('2h') == timedelta(hours=2)
    assert parse_time_string('1d') == timedelta(days=1)
    assert parse_time_string('1w') == timedelta(weeks=1)
    assert parse_time_string('1y') == timedelta(days=365)
    assert parse_time_string('all') is None

    with pytest.raises(ValueError):
        parse_time_string('invalid')

def test_get_search_criteria(config):
    """Test IMAP search criteria generation"""
    # Test with default config (all emails, exclude tagged)
    criteria = get_search_criteria(config)
    assert criteria == '(NOT KEYWORD paperless)'

    # Test with time limit
    config['time_limit'] = '1d'
    criteria = get_search_criteria(config)
    expected_date = datetime.now() - timedelta(days=1)
    assert 'SINCE' in criteria
    assert expected_date.strftime("%d-%b-%Y") in criteria
    assert 'NOT KEYWORD paperless' in criteria

    # Test without tag exclusion
    config['tag_name'] = None
    criteria = get_search_criteria(config)
    assert 'KEYWORD' not in criteria
    assert 'SINCE' in criteria

@patch('time.sleep')
def test_main_with_interval(mock_sleep):
    """Test main loop with interval"""
    mock_args = MagicMock()
    mock_args.time_limit = None
    mock_args.interval = '30m'

    mock_config = {
        'email': 'test@example.com',
        'password': 'secret',
        'interval': '30m',
        'time_limit': 'all'
    }

    with patch('sorti.main.parse_arguments', return_value=mock_args), \
         patch('sorti.main.load_config', return_value=mock_config), \
         patch('sorti.main.process_mailbox') as mock_process:

        # Simuliere einen KeyboardInterrupt nach dem ersten Durchlauf
        mock_process.side_effect = KeyboardInterrupt()

        from sorti.main import main
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        mock_process.assert_called_once()

def test_process_emails_with_tag_filter(mock_imap_class, mock_imap, config):
    """Test email processing with tag filtering"""
    mock_imap_class.return_value = mock_imap

    # Mock email search to verify search criteria
    mock_imap.search.return_value = ('OK', [b'1'])

    # Create a test email
    email_content = b"""From: sender@example.com
Subject: Test Invoice
Content-Type: text/plain

This is a test invoice email."""

    mock_imap.fetch.return_value = ('OK', [(b'1', email_content)])

    # Process emails
    process_emails(mock_imap, 'INBOX', config)

    # Verify that search included tag filtering
    search_args = mock_imap.search.call_args[0]
    assert any('NOT KEYWORD paperless' in str(arg) for arg in search_args)
