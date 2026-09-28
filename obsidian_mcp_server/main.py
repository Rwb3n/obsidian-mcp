# Remove FastAPI imports as FastMCP handles the server internally
# from fastapi import FastAPI, HTTPException
# from typing import Any

# Placeholder for SDK Request type - No longer needed here
# class MCPRequest:
#     action: str
#     params: dict

# Import the FastMCP application instance from mcp_server
# Use absolute import based on package structure
from obsidian_mcp_server.mcp_server import mcp_app

# Import logging and config
import logging
from obsidian_mcp_server.config import settings

logger = logging.getLogger("obsidian_mcp_server")

# Configure logging explicitly for DEBUG level
# Remove previous explicit logger configuration block
# app_logger = logging.getLogger("obsidian_mcp_server") 
# ... (removed block)
# --- End explicit logger configuration ---

# --- Uvicorn Logging Configuration --- 
# Define a config dict for Uvicorn to use
# https://docs.python.org/3/library/logging.config.html#configuration-dictionary-schema
# https://www.uvicorn.org/settings/#logging
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False, # Keep existing loggers (like uvicorn's)
    "formatters": {
        "default": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stderr", # Log to stderr
        },
    },
    "loggers": {
        "uvicorn": {"handlers": ["default"], "level": "INFO"}, # Keep uvicorn INFO
        "uvicorn.error": {"level": "INFO"},
        "uvicorn.access": {"handlers": ["default"], "level": "INFO"},
        # --- Set our application logger to DEBUG ---
        "obsidian_mcp_server": {
            "handlers": ["default"],
            "level": "DEBUG",
            # "propagate": False, # Try removing this - let messages propagate
        },
        # Explicitly set the vault_writer logger to DEBUG
        "obsidian_mcp_server.utils.vault_writer": {
            "handlers": ["default"],
            "level": "DEBUG",
            "propagate": True, # Ensure messages also go to parent if needed
        },
        # --- End application logger config ---
    },
}
# --- End Uvicorn Logging Configuration ---

# --- Main Execution Block ---
def main():
    # Log to stderr only: with the stdio transport, stdout carries the MCP protocol.
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    transport = settings.server_transport
    if transport == "stdio":
        logger.info("Starting Obsidian MCP Server on stdio")
    else:
        logger.info(f"Starting Obsidian MCP Server ({transport}) on http://{settings.server_host}:{settings.server_port}")
    mcp_app.run(transport=transport)


if __name__ == "__main__":
    main()

# Remove old FastAPI app instantiation and uvicorn.run call
# app = FastAPI(...) 
# uvicorn.run(app, ...) 