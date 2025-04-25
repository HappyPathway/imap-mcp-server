# IMAP MCP Server

## Installation

1. Clone the repository
2. Make the setup script executable:
   ```bash
   chmod +x setup.sh
   ```
3. Run the setup script:
   ```bash
   ./setup.sh
   ```
4. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

## Running the Server

```bash
python src/server.py
```

## Development

Make sure to activate the virtual environment before running or developing:

```bash
source venv/bin/activate
```

To install new dependencies:

```bash
pip install <package>
pip freeze > requirements.txt
```
