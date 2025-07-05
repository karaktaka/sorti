# IMAP Email Processor

A Python tool for automatically processing emails via IMAP. It searches emails for important documents and invoices and marks them with a configurable tag.

## Features

- Automatic scanning of all IMAP folders
- Flexible configuration via YAML, environment variables, or command-line arguments
- Detection of important documents using keywords
- Detection of emails with attachments
- Exclusion of specific folders (e.g., Spam, Trash)
- Time-based email filtering (process emails from last X minutes/hours/days)
- Automatic re-processing at configurable intervals
- Skip already tagged emails
- Docker deployment support

## Installation

### Using Python

1. Install Python 3.13 or higher
2. Clone repository
3. Install dependencies:
   ```bash
   uv sync
   ```

### Using Docker

```bash
docker pull ghcr.io/karaktaka/sorti:latest

# or build locally:
docker compose build
```

## Configuration

Configuration can be done in three ways (in ascending priority):
1. YAML configuration file
2. Environment variables
3. Command-line arguments

### YAML Configuration

Copy `config.example.yaml` to `config.yaml` and adjust the values:

```yaml
# Email configuration
email: your_email@mailbox.org
password: your_password
server: imap.mailbox.org
port: 993

# Filter settings
keywords:
  - rechnung
  - invoice
  - document
  - dokument
  - vertrag
  - contract
tag_name: paperless

# Time settings
time_limit: all  # Options: "5m", "2h", "1d", "1w", "1y" or "all"
interval: 30m    # Optional: "30m", "1h", "1d" etc. for periodic execution

# Folder settings
excluded_folders:
  - Spam
  - Trash
  - Archive
  - Deleted Items
  - Archives
  - Junk
```

### Environment Variables

- `EMAIL`: Email address
- `PASSWORD`: Password
- `IMAP_SERVER`: IMAP server (default: imap.mailbox.org)
- `IMAP_PORT`: IMAP port (default: 993)
- `KEYWORDS`: Comma-separated list of keywords
- `TAG_NAME`: Tag name for marked emails
- `EXCLUDED_FOLDERS`: Comma-separated list of folders to exclude
- `TIME_LIMIT`: Time limit for email processing (e.g., "5m", "2h", "1d", "1w", "1y" or "all")
- `INTERVAL`: Interval for automatic re-processing (e.g., "30m", "1h", "1d")

### Command-line Arguments

```bash
python main.py --help
```

Available options:
- `-c, --config`: Path to configuration file (default: config.yaml)
- `--email`: Email address
- `--password`: Password
- `--server`: IMAP server
- `--port`: IMAP port
- `--keywords`: Comma-separated list of keywords
- `--tag`: Tag name
- `--exclude`: Comma-separated list of folders to exclude
- `--time-limit`: Time limit for email processing
- `--interval`: Interval for automatic re-processing

## Usage

### With Python

```bash
# Process all untagged emails
python main.py

# Process emails from last 2 hours
python main.py --time-limit 2h

# Process emails from last week and repeat every hour
python main.py --time-limit 1w --interval 1h
```

### With Docker

```bash
# Using environment variables
docker compose up -d

# Or directly with docker run
docker run -v ./config.yaml:/app/config.yaml:ro \
  -e EMAIL=your@email.com \
  -e PASSWORD=yourpassword \
  -e TIME_LIMIT=2h \
  -e INTERVAL=30m \
  ghcr.io/karaktaka/sorti:latest
```

## Time Format

The time values for `--time-limit` and `--interval` support the following formats:
- `Xm`: X minutes (e.g., "5m", "30m")
- `Xh`: X hours (e.g., "1h", "12h")
- `Xd`: X days (e.g., "1d", "7d")
- `Xw`: X weeks (e.g., "1w", "2w")
- `Xy`: X years (e.g., "1y")
- `all`: Process all emails (only for time-limit)

## Development

### Running Tests

```bash
pytest
```

### Building Docker Image

```bash
docker compose build
```

## License

MIT
