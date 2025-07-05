import argparse
import email
import imaplib
import os
import sys
import time
from datetime import datetime, timedelta
from email.header import decode_header
from pathlib import Path
from typing import Dict, List, Union

import yaml


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='IMAP email processor for mailbox.org')
    parser.add_argument('-c', '--config',
                        type=str,
                        default='config.yaml',
                        help='Path to configuration file (default: config.yaml)')
    parser.add_argument('--email',
                        help='Email address (overrides config file)')
    parser.add_argument('--password',
                        help='Email password (overrides config file)')
    parser.add_argument('--server',
                        help='IMAP server (overrides config file)')
    parser.add_argument('--port',
                        type=int,
                        help='IMAP port (overrides config file)')
    parser.add_argument('--keywords',
                        help='Comma-separated list of keywords (overrides config file)')
    parser.add_argument('--tag',
                        help='Tag name for important documents (overrides config file)')
    parser.add_argument('--exclude',
                        help='Comma-separated list of folders to exclude (overrides config file)')
    parser.add_argument('--time-limit',
                        help='Time limit for email processing (e.g., "5m", "2h", "1d", "1w", "1y" or "all")')
    parser.add_argument('--interval',
                        help='Interval for script execution (e.g., "30m", "1h", "1d")')

    return parser.parse_args()


def load_config(args: argparse.Namespace) -> Dict:
    """Load configuration from config file and command line arguments"""
    config = {
        'email': None,
        'password': None,
        'server': 'imap.mailbox.org',
        'port': 993,
        'keywords': ['rechnung', 'invoice', 'document', 'dokument', 'vertrag', 'contract'],
        'tag_name': 'paperless',
        'excluded_folders': ['Spam', 'Trash', 'Archive', 'Papierkorb', 'Archiv', 'Junk'],
        'time_limit': 'all',
        'interval': None
    }

    # Load from YAML config file if it exists
    if Path(args.config).exists():
        try:
            with open(args.config, 'r') as f:
                yaml_config = yaml.safe_load(f)
                if yaml_config:
                    for key in config.keys():
                        if key in yaml_config:
                            config[key] = yaml_config[key]
        except Exception as e:
            print(f"Error reading configuration file: {e}")

    # Override with environment variables
    if os.getenv('EMAIL'): config['email'] = os.getenv('EMAIL')
    if os.getenv('PASSWORD'): config['password'] = os.getenv('PASSWORD')
    if os.getenv('IMAP_SERVER'): config['server'] = os.getenv('IMAP_SERVER')
    if os.getenv('IMAP_PORT'): config['port'] = int(os.getenv('IMAP_PORT'))
    if os.getenv('KEYWORDS'): config['keywords'] = [k.strip() for k in os.getenv('KEYWORDS').split(',') if k.strip()]
    if os.getenv('TAG_NAME'): config['tag_name'] = os.getenv('TAG_NAME')
    if os.getenv('EXCLUDED_FOLDERS'):
        config['excluded_folders'] = [f.strip() for f in os.getenv('EXCLUDED_FOLDERS').split(',') if f.strip()]
    if os.getenv('TIME_LIMIT'): config['time_limit'] = os.getenv('TIME_LIMIT')
    if os.getenv('INTERVAL'): config['interval'] = os.getenv('INTERVAL')

    # Override with command line arguments (highest priority)
    if args.email: config['email'] = args.email
    if args.password: config['password'] = args.password
    if args.server: config['server'] = args.server
    if args.port: config['port'] = args.port
    if args.keywords: config['keywords'] = [k.strip() for k in args.keywords.split(',') if k.strip()]
    if args.tag: config['tag_name'] = args.tag
    if args.exclude:
        config['excluded_folders'] = [f.strip() for f in args.exclude.split(',') if f.strip()]
    if args.time_limit: config['time_limit'] = args.time_limit
    if args.interval: config['interval'] = args.interval

    # Check required values
    if not config['email'] or not config['password']:
        raise ValueError("Email and password must be configured!")

    return config


def connect_to_mailbox(config: Dict):
    """Establish connection to IMAP server"""
    imap = imaplib.IMAP4_SSL(config['server'], config['port'])
    imap.login(config['email'], config['password'])
    return imap


def is_important_document(subject: str, body: str, keywords: List[str]) -> bool:
    """Check if the email contains an important document"""
    subject_lower = subject.lower()
    body_lower = body.lower()
    return any(keyword in subject_lower or keyword in body_lower for keyword in keywords)


def get_all_folders(imap):
    """Retrieve all available folders"""
    folders = []
    for folder in imap.list()[1]:
        folder_name = folder.decode().split('"/"')[-1].strip('" ')
        folders.append(folder_name)
    return folders


def parse_time_string(time_str: str) -> Union[timedelta, None]:
    """Convert time string to timedelta object"""
    if time_str == 'all':
        return None

    value = int(time_str[:-1])
    unit = time_str[-1].lower()

    if unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    elif unit == 'w':
        return timedelta(weeks=value)
    elif unit == 'y':
        return timedelta(days=value*365)
    else:
        raise ValueError(f"Invalid time unit: {unit}. Use m (minutes), h (hours), d (days), w (weeks), or y (years)")


def get_search_criteria(config: Dict) -> str:
    """Generate IMAP search criteria based on configuration"""
    criteria = []

    # Add time limit if specified
    if config['time_limit'] != 'all':
        time_delta = parse_time_string(config['time_limit'])
        if time_delta:
            date_str = (datetime.now() - time_delta).strftime("%d-%b-%Y")
            criteria.append(f'SINCE {date_str}')

    # Exclude messages that already have the tag
    if config['tag_name']:
        criteria.append(f'NOT KEYWORD {config["tag_name"]}')

    return '(' + ' '.join(criteria) + ')' if criteria else 'ALL'


def process_emails(imap, folder: str, config: Dict):
    """Process emails in a folder"""
    imap.select(folder)
    search_criteria = get_search_criteria(config)
    _, messages = imap.search(None, search_criteria)

    for message_num in messages[0].split():
        _, msg_data = imap.fetch(message_num, '(RFC822)')
        email_body = msg_data[0][1]
        message = email.message_from_bytes(email_body)

        # Decode email subject
        subject = ""
        if message["subject"]:
            subject = decode_header(message["subject"])[0][0]
            if isinstance(subject, bytes):
                try:
                    subject = subject.decode()
                except Exception as e:
                    print(f"Error decoding subject: {e}")
                    subject = ""

        # Extract email text
        body = ""
        if message.is_multipart():
            for part in message.walk():
                if part.get_content_type() == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                    except Exception as e:
                        print(f"Error decoding body: {e}")
                    break
        else:
            try:
                body = message.get_payload(decode=True).decode()
            except Exception as e:
                print(f"Error decoding body: {e}")

        # Check for important documents
        if is_important_document(subject, body, config['keywords']) or \
                (message.is_multipart() and any(part.get_content_type().startswith('application/') for part in message.walk())):
            # Set configured tag
            if config["tag_name"]:
                try:
                    # print(f"Setting tag '{config['tag_name']}' for message {subject} in folder '{folder}'")
                    imap.store(message_num, '+FLAGS', f'({config["tag_name"]})')
                except Exception as e:
                    print(f"Error setting tag for message {message_num}: {e}")


def should_process_folder(folder_name: str, excluded_folders: List[str]) -> bool:
    """Check if the folder should be processed based on exclusion list"""
    return not any(excluded.lower() in folder_name.lower() for excluded in excluded_folders)


def process_mailbox(config: Dict):
    """Process all folders in the mailbox"""
    try:
        # Connect and process emails
        imap = connect_to_mailbox(config)
        folders = get_all_folders(imap)

        for folder in folders:
            try:
                if should_process_folder(folder, config['excluded_folders']):
                    print(f"Processing folder: {folder}")
                    process_emails(imap, folder, config)
                else:
                    print(f"Skipping excluded folder: {folder}")
            except Exception as e:
                print(f"Error processing folder {folder}: {str(e)}")

        imap.logout()
    except Exception as e:
        print(f"Error processing mailbox: {str(e)}")


def main():
    try:
        # Parse command line arguments
        args = parse_arguments()

        # Load configuration
        config = load_config(args)

        # Main processing loop
        while True:
            print(f"\nStarting email processing at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            process_mailbox(config)

            if not config['interval']:
                break

            interval = parse_time_string(config['interval'])
            print(f"Waiting {config['interval']} until next run...")
            time.sleep(interval.total_seconds())

    except KeyboardInterrupt:
        print("\nProcess terminated by user")
        sys.exit(0)
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
