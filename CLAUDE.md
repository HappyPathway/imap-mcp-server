# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build Commands
- Setup: `chmod +x setup.sh && ./setup.sh`
- Activate environment: `source venv/bin/activate`
- Run server: `python src/server.py`
- Install dependencies: `pip install <package> && pip freeze > requirements.txt`

## Code Style Guidelines
- **Imports**: Standard imports first, third-party second, local modules last with blank lines between groups
- **Type Annotations**: Use typing module for all function parameters and return types
- **Naming**: Classes=PascalCase, functions/variables=snake_case, constants=UPPER_SNAKE_CASE
- **Documentation**: Google-style docstrings with Args/Returns sections
- **Error Handling**: Use try/except with proper logging and session rollbacks for database operations
- **Database**: Use context manager pattern for sessions, proper transaction handling
- **MCP Tools**: Define with `@mcp.tool()` decorator, implement async functions
- **Environment**: Load configuration from .env files using python-dotenv

## Project Structure
The project implements an IMAP MCP server that provides email-related tools via MCP protocol.
Key components are in src/ including server.py (main entry point), models.py (database models),
and tools/ (MCP tool implementations).