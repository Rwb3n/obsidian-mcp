# Import the configured FastMCP app instance
from obsidian_mcp_server.mcp_server import mcp_app

# Note: We don't need to import settings or uvicorn here anymore
# FastMCP's run() method will handle using the configured host/port internally.

if __name__ == "__main__":
    # Use the built-in run method of FastMCP
    mcp_app.run() 