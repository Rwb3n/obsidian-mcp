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
from obsidian_mcp_server.config import settings # Assuming config might be needed

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
if __name__ == "__main__":
    # Configuration (use settings from config.py if available)
    HOST = settings.server_host # Get host from config
    PORT = settings.server_port # Get port from config

    print(f"Starting Obsidian MCP Server (via FastMCP internal server) on http://{HOST}:{PORT}")
    
    # Directly run the FastMCP app, specifying SSE transport
    # Host/Port are configured during FastMCP initialization in mcp_server.py
    # log_config is not directly supported by FastMCP.run() (uses internal logging)
    try:
        mcp_app.run(transport="sse") # Specify transport="sse"
    except Exception as run_e:
         print(f"An unexpected error occurred trying to run the MCP server: {run_e}")

# Remove old FastAPI app instantiation and uvicorn.run call
# app = FastAPI(...) 
# uvicorn.run(app, ...) 