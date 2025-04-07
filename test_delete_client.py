# test_delete_client.py

import asyncio
# Import the necessary components
from mcp.client.sse import sse_client # Low-level SSE connection
from mcp.client.session import ClientSession # High-level session
import os # Needed for joining path

# --- Configuration ---
# !! Important: Ensure this matches the VAULT_PATH used by the server !!
#    Ideally, read from config, but hardcoding for simplicity here.
#    Make sure the path exists and is correct.
VAULT_BASE_PATH = r"D:\Documents\OBSIDIAN\OBSIDIAN - Copy"
# Point to the default SSE path used by FastMCP
SERVER_URL = "http://localhost:8000/sse" # Changed path to /sse
# Use a unique name for the note to be deleted
TEST_NOTE_REL_PATH = "_MCP_Test_Delete_Note.md"
TEST_NOTE_ABS_PATH = os.path.join(VAULT_BASE_PATH, TEST_NOTE_REL_PATH)

async def run_delete_test():
    """Runs the test sequence for deleting a note."""
    print(f"--- Starting Delete Note Test ---")
    print(f"Server URL: {SERVER_URL}")
    print(f"Test Note Path: {TEST_NOTE_REL_PATH}")

    # Ensure the test note doesn't exist initially (optional cleanup)
    if os.path.exists(TEST_NOTE_ABS_PATH):
        print(f"WARN: Pre-existing test file found. Attempting removal: {TEST_NOTE_ABS_PATH}")
        try:
            os.remove(TEST_NOTE_ABS_PATH)
            print("  Pre-existing file removed.")
        except OSError as e:
            print(f"  ERROR: Could not remove pre-existing file: {e}. Exiting.")
            return

    # Use the correct function name: sse_client
    print("\nAttempting to connect to server and initialize session...")
    try:
        async with sse_client(SERVER_URL) as streams: # Use low-level sse_client
            read_stream, write_stream = streams # Unpack the streams
            # Now create the high-level session using the streams
            async with ClientSession(read_stream, write_stream) as session: 
                print("  Streams connected. Initializing MCP Session...")
                await session.initialize() # Initialize the session (perform handshake)
                print("  MCP Session Initialized. Connected to server.")

                # 1. Create the note to be deleted
                create_args = {
                    "relative_note_path": TEST_NOTE_REL_PATH,
                    "content": "This note is created only to be deleted.",
                    "metadata": {"status": "to_be_deleted"},
                    "overwrite": True # Ensure we can run the test multiple times
                }
                print(f"\nCalling tool: create_note with args: {create_args['relative_note_path']}")
                try:
                    # Use the session object which has call_tool
                    create_result = await session.call_tool("create_note", arguments=create_args)
                    # Check result structure (call_tool returns result object, not boolean directly)
                    if create_result and create_result.content and getattr(create_result.content[0], 'text', '').lower() == 'true':
                        print("  Tool create_note successful.")
                    else:
                        print(f"  Tool create_note FAILED or returned unexpected content: {create_result}. Exiting test.")
                        return # Cannot proceed if creation fails
                except Exception as e:
                    print(f"  Tool create_note FAILED with exception: {e}. Exiting test.")
                    return

                # 2. Verify creation (optional, but good practice)
                print(f"\nCalling tool: get_note_content (to verify creation) with args: {TEST_NOTE_REL_PATH}")
                try:
                    verify_create_result = await session.call_tool("get_note_content", arguments={"note_path": TEST_NOTE_REL_PATH})
                    if verify_create_result and verify_create_result.content: # Check content exists
                         print("  Verification PASSED: Note content retrieved successfully after creation.")
                    else:
                         print(f"  Verification FAILED: Could not get content after creation: {verify_create_result}. Exiting test.")
                         # Attempt cleanup before exiting
                         try:
                             print("  Attempting cleanup by deleting note...")
                             await session.call_tool("delete_note", arguments={"note_path": TEST_NOTE_REL_PATH})
                         except Exception as cleanup_e:
                             print(f"  Cleanup delete attempt failed: {cleanup_e}")
                         return
                except Exception as e:
                    print(f"  Verification FAILED with exception: {e}. Exiting test.")
                    # Attempt cleanup before exiting
                    try:
                         print("  Attempting cleanup by deleting note...")
                         await session.call_tool("delete_note", arguments={"note_path": TEST_NOTE_REL_PATH})
                    except Exception as cleanup_e:
                         print(f"  Cleanup delete attempt failed: {cleanup_e}")
                    return

                # 3. Delete the note
                delete_args = {"relative_note_path": TEST_NOTE_REL_PATH}
                print(f"\nCalling tool: delete_note with args: {delete_args['relative_note_path']}")
                try:
                    delete_result = await session.call_tool("delete_note", arguments=delete_args)
                    # Check result structure
                    if delete_result and delete_result.content and getattr(delete_result.content[0], 'text', '').lower() == 'true':
                         print("  Tool delete_note successful (returned True).")
                    else:
                         print(f"  Tool delete_note FAILED or returned unexpected content: {delete_result}. Exiting test.")
                         return
                except Exception as e:
                    print(f"  Tool delete_note FAILED with exception: {e}. Exiting test.")
                    return

                # 4. Verify deletion
                print(f"\nCalling tool: get_note_content (to verify deletion) with args: {TEST_NOTE_REL_PATH}")
                try:
                    verify_delete_result = await session.call_tool("get_note_content", arguments={"note_path": TEST_NOTE_REL_PATH})
                    
                    # Correct Verification: Check the isError flag primarily
                    if verify_delete_result and getattr(verify_delete_result, 'isError', False):
                         print("  Verification PASSED: Tool get_note_content returned an error as expected after deletion.")
                         # Optionally check the error message within the content
                         try:
                             error_text = getattr(verify_delete_result.content[0], 'text', '')
                             if "note not found" in error_text.lower():
                                 print(f"    Error message confirms 'Note not found': \"{error_text}\"")
                             else:
                                 print(f"    Error message was different than expected: \"{error_text}\"")
                         except (IndexError, AttributeError):
                            print("    Could not extract error message text from content.")
                            
                    # Check if it erroneously succeeded (isError is False/missing but content exists)
                    elif verify_delete_result and not getattr(verify_delete_result, 'isError', True) and verify_delete_result.content:
                         print("  Verification FAILED: Tool get_note_content succeeded after deletion, note likely still exists.")
                         print(f"    Unexpected result received: {verify_delete_result!r}")
                    else:
                         # Catch other unexpected response structures
                         print(f"  Verification FAILED: Unexpected response structure from get_note_content after deletion: {verify_delete_result!r}")

                except Exception as e:
                    # This exception block might not be strictly necessary if call_tool always returns a result object,
                    # but keep it for robustness.
                     print(f"  Verification FAILED with exception during get_note_content call: {e}")

    except Exception as connect_e:
        print(f"\nFATAL: Failed to connect or initialize session: {connect_e}")

    print(f"\n--- Delete Note Test Finished ---")

if __name__ == "__main__":
    # Basic check for vault path
    if not os.path.isdir(VAULT_BASE_PATH):
        print(f"ERROR: VAULT_BASE_PATH does not exist or is not a directory: {VAULT_BASE_PATH}")
        print("Please ensure the path is correct and the directory exists.")
    else:
        asyncio.run(run_delete_test())