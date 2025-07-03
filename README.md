# IMAP Email Processor

A Python tool for automatically processing emails via IMAP. It searches emails for important documents and invoices and marks them with a configurable tag.

## Features

- Automatic scanning of all IMAP folders
- Flexible configuration via YAML, environment variables, or command-line arguments
- Detection of important documents using keywords
- Detection of emails with attachments
- Exclusion of specific folders (e.g., Spam, Trash)
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

## Usage

### With Python

```bash
# With default configuration file
python main.py

# With specific configuration file
python main.py -c my_config.yaml

# With command-line arguments
python main.py --email user@mailbox.org --password secret --keywords "invoice,contract"
```

### With Docker

```bash
# With configuration file
docker run -v $(pwd)/config.yaml:/app/config.yaml ghcr.io/yourusername/imap-processor

# With environment variables
docker run -e EMAIL=user@mailbox.org -e PASSWORD=secret ghcr.io/yourusername/imap-processor

# With Docker Compose
docker compose up
```

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
