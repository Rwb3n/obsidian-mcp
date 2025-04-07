import asyncio
import sys
import httpx # Import httpx for specific connection errors
import os # Added for cleanup

# Import the correct client and base types
# from mcp import ClientSession, types # Incorrect import
from mcp.client.session import ClientSession # Correct import
from mcp.client.sse import sse_client
from mcp import types # Keep types import if needed elsewhere
# Import settings to get vault path for cleanup
from obsidian_mcp_server.config import settings

# Placeholder connect_to_server function is no longer needed
# async def connect_to_server(url: str):
#    ...

async def run_test():
    server_url = "http://127.0.0.1:8000" # Make sure this matches the running server
    # Explicitly try connecting to the /sse path, as seen in SDK examples
    sse_endpoint_url = f"{server_url}/sse"
    test_note_rel_path = "_MCP_Test_Client_Note.md"
    test_note_full_path = os.path.join(settings.obsidian_vault_path, test_note_rel_path)

    try:
        print(f"Attempting to connect to {sse_endpoint_url} using sse_client...")
        # Use the correct sse_client directly
        async with sse_client(sse_endpoint_url) as (read, write):
            print("Connection successful, streams obtained.")
            # Sampling callback is optional for testing tools
            async with ClientSession(read, write) as session:
                print("Initializing session...")
                await session.initialize()
                print("Session initialized.")

                # --- Test a tool --- 
                tool_name = "list_notes"
                tool_args = {"relative_path": "."} # Test listing root
                print(f"\nCalling tool: {tool_name} with args: {tool_args}")

                try:
                    result = await session.call_tool(tool_name, arguments=tool_args)
                    print(f"Tool '{tool_name}' successful.")
                    print("Result:", result)
                    # Note: The exact structure of 'result' depends on the SDK's response handling.
                    # It might be the direct return value, or wrapped in an object.

                except Exception as tool_error:
                    print(f"Error calling tool {tool_name}: {tool_error}")

                # --- Add more tool tests here ---

                # --- Test search_notes_content --- 
                search_tool = "search_notes_content"
                search_term = "Obsidian" # Assuming this is in README.md
                search_args = {"query": search_term}
                print(f"\nCalling tool: {search_tool} with args: {search_args}")
                try:
                    result = await session.call_tool(search_tool, arguments=search_args)
                    if result and not getattr(result, 'isError', True):
                        print(f"Tool {search_tool} successful.")
                        # Result should be a list of paths (wrapped in TextContent)
                        found_paths = []
                        if result.content and isinstance(result.content, list):
                            for item in result.content:
                                path = getattr(item, 'text', None)
                                if path:
                                    found_paths.append(path)
                        
                        print(f"  Found paths: {found_paths}")
                        # Basic check: Does it contain README.md?
                        if "README.md" in found_paths:
                             print("  Verification PASSED: README.md found in search results.")
                        else:
                             print("  Verification FAILED: README.md *not* found in search results.")

                    else:
                        print(f"Tool {search_tool} FAILED: Received error response: {result}")
                except Exception as tool_error:
                    print(f"Tool {search_tool} FAILED: Exception: {tool_error}")

                # --- Test get_note_content (Success) ---
                get_content_tool = "get_note_content"
                # Use a file we know exists (assuming vault root)
                get_content_args = {"note_path": "README.md"} 
                print(f"\nCalling tool: {get_content_tool} with args: {get_content_args}")
                try:
                    result = await session.call_tool(get_content_tool, arguments=get_content_args)
                    if result and not getattr(result, 'isError', True):
                        print(f"Tool {get_content_tool} successful.")
                        # Extract text content (assuming it's wrapped like list_notes)
                        if result.content and isinstance(result.content, list) and len(result.content) > 0:
                             # Assuming the content is in the first TextContent object
                             returned_text = getattr(result.content[0], 'text', None)
                             if returned_text is not None:
                                 print(f"  Content starts with: \n---\n{returned_text[:150]}...\n---")
                             else:
                                 print("  Response content format unexpected.")
                        else:
                             print(f"  Response content unexpected: {result.content}")
                    else:
                        print(f"Tool {get_content_tool} FAILED: Received error response: {result}")
                except Exception as tool_error:
                    print(f"Tool {get_content_tool} FAILED: Exception: {tool_error}")

                # --- Test create_note --- 
                create_tool = "create_note"
                create_args = {
                    "relative_note_path": test_note_rel_path,
                    "content": "# Test Note\nCreated by MCP test client.",
                    "metadata": {"tag": "mcp-test", "status": "temp"}
                }
                print(f"\nCalling tool: {create_tool} with args: {create_args['relative_note_path']}")
                try:
                    result = await session.call_tool(create_tool, arguments=create_args)
                    # For tools returning boolean, primarily check if an error occurred.
                    # FastMCP seems to wrap bool True as TextContent("true").
                    if result and not getattr(result, 'isError', True):
                        print(f"Tool {create_tool} successful (No error reported).")
                        # Optional: Verify file existence
                        if os.path.exists(test_note_full_path):
                            print(f"  Verification PASSED: Test file found at {test_note_full_path}")
                        else:
                             print(f"  Verification FAILED: Test file NOT found at {test_note_full_path}")
                             # This would indicate an internal inconsistency
                    else:
                        print(f"Tool {create_tool} FAILED: Response indicates error: {result}")
                    # --- Add Verification for initial metadata ---
                    if result and not getattr(result, 'isError', True) and os.path.exists(test_note_full_path):
                        try:
                            verify_meta_args = {"note_path": test_note_rel_path}
                            verify_meta_result = await session.call_tool("get_note_metadata", arguments=verify_meta_args)
                            if verify_meta_result and not getattr(verify_meta_result, 'isError', True) and verify_meta_result.content:
                                import json
                                try:
                                    initial_metadata = json.loads(getattr(verify_meta_result.content[0], 'text', '{}'))
                                    if initial_metadata.get("tag") == "mcp-test" and initial_metadata.get("status") == "temp":
                                        print(f"  Verification PASSED: Initial metadata found correctly after create.")
                                    else:
                                        print(f"  Verification FAILED: Initial metadata mismatch after create. Found: {initial_metadata}")
                                except json.JSONDecodeError:
                                    print(f"  Verification FAILED: Could not parse initial metadata JSON: {getattr(verify_meta_result.content[0], 'text', '')}")
                            else:
                                print(f"  Verification FAILED: Could not retrieve initial metadata after create. Response: {verify_meta_result}")
                        except Exception as verify_meta_e:
                            print(f"  Verification FAILED: Error retrieving initial metadata: {verify_meta_e}")
                    # --- End Verification ---
                except Exception as tool_error:
                     print(f"Tool {create_tool} FAILED: Exception: {tool_error}")
                
                # --- Test edit_note ---
                edit_tool = "edit_note"
                edit_args = {
                    "relative_note_path": test_note_rel_path,
                    "new_content": "# Test Note (Edited)\nThis content has been modified.",
                    "backup": True # Test with backup
                }
                print(f"\nCalling tool: {edit_tool} with args: {edit_args['relative_note_path']}")
                try:
                    result = await session.call_tool(edit_tool, arguments=edit_args)
                    # Check for error response
                    if result and not getattr(result, 'isError', True):
                        print(f"Tool {edit_tool} successful.")
                        # Add verification (optional)
                        # try:
                        #     verify_result = await session.call_tool("get_note_content", {"note_path": test_note_rel_path})
                        #     if verify_result and not getattr(verify_result, 'isError', True) and verify_result.content:
                        #         retrieved_content = getattr(verify_result.content[0], 'text', '')
                        #         if "(Edited)" in retrieved_content:
                        #             print(f"  Verification PASSED: Edited content found.")
                        #         else:
                        #             print(f"  Verification FAILED: Edited content NOT found.")
                        #     else:
                        #         print(f"  Verification FAILED: Could not retrieve content after edit.")
                        # except Exception as verify_e:
                        #     print(f"  Verification FAILED: Error retrieving content after edit: {verify_e}")
                    else:
                        print(f"Tool {edit_tool} FAILED: Response indicates error: {result}")
                except Exception as tool_error:
                    print(f"Tool {edit_tool} FAILED: Exception: {tool_error}")

                # --- Test append_to_note ---
                append_tool = "append_to_note"
                append_content = "\n\n---\nAppended content."
                append_args = {
                    "relative_note_path": test_note_rel_path,
                    "content": append_content,
                    "backup": False
                }
                print(f"\nCalling tool: {append_tool} with args: {append_args['relative_note_path']}")
                try:
                    result = await session.call_tool(append_tool, arguments=append_args)
                    # Check for error response
                    if result and not getattr(result, 'isError', True):
                         print(f"Tool {append_tool} successful.")
                        # Add verification (optional)
                        # try:
                        #     verify_result = await session.call_tool("get_note_content", {"note_path": test_note_rel_path})
                        #     if verify_result and not getattr(verify_result, 'isError', True) and verify_result.content:
                        #         retrieved_content = getattr(verify_result.content[0], 'text', '')
                        #         if "Appended content." in retrieved_content and "(Edited)" in retrieved_content:
                        #             print(f"  Verification PASSED: Appended content found.")
                        #         else:
                        #             print(f"  Verification FAILED: Appended content NOT found.")
                        #     else:
                        #         print(f"  Verification FAILED: Could not retrieve content after append.")
                        # except Exception as verify_e:
                        #     print(f"  Verification FAILED: Error retrieving content after append: {verify_e}")
                    else:
                        print(f"Tool {append_tool} FAILED: Response indicates error: {result}")
                except Exception as tool_error:
                    print(f"Tool {append_tool} FAILED: Exception: {tool_error}")

                # --- Test update_note_metadata ---
                update_tool = "update_note_metadata" # Use original tool name
                update_args = {
                    "relative_note_path": test_note_rel_path,
                    "metadata_updates": {"status": "updated", "tested": True, "new_key": "new_value", "tag": None}, # Use None to remove tag
                    "backup": True
                }
                print(f"\nCalling tool: {update_tool} with args: {update_args['relative_note_path']}")
                try:
                    result = await session.call_tool(update_tool, arguments=update_args)
                    # Check for error response from the update tool itself
                    if result and not getattr(result, 'isError', True):
                        print(f"Tool {update_tool} successful.")
                        
                        # --- Verification Step: Call get_note_metadata --- 
                        print("  Attempting verification by calling get_note_metadata...")
                        try: 
                            verify_meta_args = {"note_path": test_note_rel_path}
                            verify_meta_result = await session.call_tool("get_note_metadata", arguments=verify_meta_args)
                            
                            if verify_meta_result and not getattr(verify_meta_result, 'isError', True) and verify_meta_result.content:
                                import json # Need json for parsing
                                try:
                                    # Parse the JSON string returned by get_note_metadata
                                    retrieved_metadata = json.loads(getattr(verify_meta_result.content[0], 'text', '{}'))
                                    print(f"  Retrieved metadata for verification: {retrieved_metadata}")

                                    # Build expected state: Should include None values sent in update
                                    expected_metadata_after_update = update_args['metadata_updates'].copy() # Start with updates
                                    # Merge with initial keys that were not updated/removed
                                    initial_keys_to_keep = {k: v for k, v in initial_metadata.items() if k not in update_args['metadata_updates']} 
                                    expected_metadata_after_update.update(initial_keys_to_keep)
                                    # NO LONGER filter out None values here, expect them back
                                    # expected_metadata_after_update = {k: v for k, v in update_args['metadata_updates'].items() if v is not None} 
                                    # initial_keys_to_keep = {k: initial_metadata.get(k) for k in initial_metadata if k not in update_args['metadata_updates']} 

                                    # Sort keys for consistent comparison
                                    retrieved_sorted = dict(sorted(retrieved_metadata.items()))
                                    expected_sorted = dict(sorted(expected_metadata_after_update.items()))
                                    
                                    if retrieved_sorted == expected_sorted:
                                        print("  Verification PASSED: Retrieved metadata matches expected state after update.")
                                    else:
                                        print(f"  Verification FAILED: Retrieved metadata mismatch.")
                                        print(f"    Expected: {expected_sorted}")
                                        print(f"    Found:    {retrieved_sorted}")
                                except json.JSONDecodeError:
                                    print(f"  Verification FAILED: Could not parse metadata JSON from get_note_metadata: {getattr(verify_meta_result.content[0], 'text', '')}")
                                except KeyError as ke:
                                    print(f"  Verification FAILED: Internal key error during verification construction: {ke}") # Should not happen now
                            else:
                                print(f"  Verification FAILED: Could not retrieve metadata after update. Response: {verify_meta_result}")
                        except Exception as verify_e:
                             print(f"  Verification FAILED: Error during get_note_metadata call for verification: {verify_e}")
                        # --- End Verification Step ---
                    else:
                        print(f"Tool {update_tool} FAILED: Response indicates error: {result}")
                except Exception as tool_error:
                    print(f"Tool {update_tool} FAILED: Exception during call: {tool_error}") # Catch errors during the *update* call

                # --- Test Error Handling (Get content of non-existent file) ---
                error_tool = "get_note_content"
                error_args = {"note_path": "__this_file_should_not_exist.md"}
                print(f"\nCalling tool: {error_tool} with invalid args: {error_args}")
                try:
                    result = await session.call_tool(error_tool, arguments=error_args)
                    # Expect an error response here
                    if result and getattr(result, 'isError', False):
                        print(f"Error test PASSED: Tool {error_tool} returned an error response as expected.")
                        # Print error details
                        print(f"  Response details: {result!r}") 
                    else:
                         print(f"Error test FAILED: Tool {error_tool} did not return an error response. Result: {result}")
                except Exception as tool_error:
                     # Some tools might raise exceptions directly on severe errors
                     print(f"Error test PASSED (via exception): Tool {error_tool} raised exception as expected: {tool_error}")

                # --- Test Daily Notes --- 
                print("\n--- Testing Daily Notes --- ")
                import datetime
                today = datetime.date.today()
                today_iso = today.isoformat()
                tomorrow = today + datetime.timedelta(days=1)
                tomorrow_iso = tomorrow.isoformat()
                
                # Calculate expected paths based on the known config
                expected_path_today = f"Journal/{today.strftime('%Y')}/{today.strftime('%m')}/{today.strftime('%Y-%m-%d')}.md"
                expected_path_tomorrow = f"Journal/{tomorrow.strftime('%Y')}/{tomorrow.strftime('%m')}/{tomorrow.strftime('%Y-%m-%d')}.md"

                # 1. Get today's daily note path
                get_path_tool = "get_daily_note_path"
                print(f"\nCalling tool: {get_path_tool} (no args - should be today)")
                try:
                    result = await session.call_tool(get_path_tool, arguments={})
                    if result and not getattr(result, 'isError', True) and result.content:
                        retrieved_path = getattr(result.content[0], 'text', '')
                        print(f"  Tool {get_path_tool} successful. Retrieved path: {retrieved_path}")
                        # Use the calculated expected path
                        if retrieved_path == expected_path_today:
                             print(f"  Verification PASSED: Retrieved path matches today's expected path.")
                        else:
                             print(f"  Verification FAILED: Retrieved path '{retrieved_path}' does not match expected '{expected_path_today}'.")
                    else:
                         print(f"Tool {get_path_tool} FAILED: {result}")
                except Exception as e:
                    print(f"Tool {get_path_tool} FAILED with exception: {e}")
                
                # 2. Get tomorrow's daily note path
                print(f"\nCalling tool: {get_path_tool} (with date: {tomorrow_iso})")
                try:
                    result = await session.call_tool(get_path_tool, arguments={"target_date_iso": tomorrow_iso})
                    if result and not getattr(result, 'isError', True) and result.content:
                        retrieved_path = getattr(result.content[0], 'text', '')
                        print(f"  Tool {get_path_tool} successful. Retrieved path: {retrieved_path}")
                        # Use the calculated expected path
                        if retrieved_path == expected_path_tomorrow:
                             print(f"  Verification PASSED: Retrieved path matches tomorrow's expected path.")
                        else:
                             print(f"  Verification FAILED: Retrieved path '{retrieved_path}' does not match expected '{expected_path_tomorrow}'.")
                    else:
                         print(f"Tool {get_path_tool} FAILED: {result}")
                except Exception as e:
                    print(f"Tool {get_path_tool} FAILED with exception: {e}")

                # 3. Create today's daily note (ensure it doesn't exist first)
                create_daily_tool = "create_daily_note"
                # Use the calculated expected path for existence check and verification
                today_expected_full_path = os.path.join(settings.obsidian_vault_path, expected_path_today)
                if os.path.exists(today_expected_full_path):
                    print(f"  WARN: Today's daily note already exists, removing for test: {today_expected_full_path}")
                    os.remove(today_expected_full_path)
                
                print(f"\nCalling tool: {create_daily_tool} (no args - should be today)")
                try:
                    result = await session.call_tool(create_daily_tool, arguments={})
                    if result and not getattr(result, 'isError', True) and result.content:
                        retrieved_path = getattr(result.content[0], 'text', '')
                        print(f"  Tool {create_daily_tool} successful. Returned path: {retrieved_path}")
                        # Use the calculated expected path for verification
                        if retrieved_path == expected_path_today and os.path.exists(today_expected_full_path):
                            print(f"  Verification PASSED: Today's daily note created at expected path.")
                        else:
                            print(f"  Verification FAILED: Path mismatch or file not found after create. Got '{retrieved_path}'. Expected '{expected_path_today}'. Exists? {os.path.exists(today_expected_full_path)}")
                    else:
                         print(f"Tool {create_daily_tool} FAILED: {result}")
                except Exception as e:
                    print(f"Tool {create_daily_tool} FAILED with exception: {e}")

                # 4. Append to today's daily note
                append_daily_tool = "append_to_daily_note"
                append_daily_content = "\nTest content appended to daily note."
                print(f"\nCalling tool: {append_daily_tool} (no date - should be today)")
                try:
                    result = await session.call_tool(append_daily_tool, arguments={"content_to_append": append_daily_content})
                    if result and not getattr(result, 'isError', True) and result.content and getattr(result.content[0], 'text', '').lower() == 'true':
                        print(f"  Tool {append_daily_tool} successful.")
                        # Verify content
                        try:
                             # Use the calculated expected path for verification
                             verify_append = await session.call_tool("get_note_content", arguments={"note_path": expected_path_today})
                             if verify_append and verify_append.content:
                                 appended_text = getattr(verify_append.content[0], 'text', '')
                                 if append_daily_content in appended_text:
                                     print("  Verification PASSED: Appended content found in daily note.")
                                 else:
                                     print("  Verification FAILED: Appended content NOT found in daily note.")
                             else:
                                 print("  Verification FAILED: Could not retrieve daily note content after append.")
                        except Exception as verify_e:
                            print(f"  Verification FAILED: Error retrieving daily note content: {verify_e}")
                    else:
                         print(f"Tool {append_daily_tool} FAILED: {result}")
                except Exception as e:
                    print(f"Tool {append_daily_tool} FAILED with exception: {e}")

                # Clean up today's daily note if created
                # Use the calculated expected path for cleanup
                today_dn_path_cleanup = os.path.join(settings.obsidian_vault_path, expected_path_today)
                if os.path.exists(today_dn_path_cleanup):
                    try:
                        os.remove(today_dn_path_cleanup)
                        print(f"Successfully deleted test file: {today_dn_path_cleanup}")
                    except Exception as cleanup_error:
                        print(f"Error deleting test file {today_dn_path_cleanup}: {cleanup_error}")
                else:
                    print(f"Test file not found for cleanup: {today_dn_path_cleanup}")

                # --- End Daily Notes Test ---

                # --- Test get_all_tags ---
                tags_tool = "get_all_tags"
                print(f"\nCalling tool: {tags_tool}")
                try:
                    result = await session.call_tool(tags_tool, arguments={})
                    if result and not getattr(result, 'isError', True) and result.content:
                        import json # For parsing the list
                        try:
                            tag_list = json.loads(getattr(result.content[0], 'text', '[]'))
                            if isinstance(tag_list, list):
                                print(f"  Tool {tags_tool} successful. Found {len(tag_list)} tags.")
                                print(f"  Tags found (first 50): {tag_list[:50]}")
                            else:
                                # Correct f-string syntax
                                content_text = getattr(result.content[0], 'text', '')
                                print(f"  Tool {tags_tool} FAILED: Result content was not a JSON list: {content_text}")
                        except json.JSONDecodeError:
                             # Correct f-string syntax
                             content_text = getattr(result.content[0], 'text', '')
                             print(f"  Tool {tags_tool} FAILED: Could not parse JSON tag list: {content_text}")
                    else:
                         print(f"Tool {tags_tool} FAILED: {result}")
                except Exception as e:
                    print(f"Tool {tags_tool} FAILED with exception: {e}")

                # --- Test get_backlinks ---
                backlinks_tool = "get_backlinks"
                backlink_target = test_note_rel_path # Use the main test note
                linking_note = "_MCP_Test_Backlink_Source.md" # Temp note to create link
                linking_note_full = os.path.join(settings.obsidian_vault_path, linking_note)
                
                print(f"\n--- Testing Backlinks for: {backlink_target} ---")
                # 1. Create linking note
                print(f"Creating temporary linking note: {linking_note}")
                try:
                    link_content = f"This note links to [[{backlink_target}]] explicitly."
                    create_link_args = {"relative_note_path": linking_note, "content": link_content}
                    link_create_res = await session.call_tool("create_note", arguments=create_link_args)
                    if not link_create_res or getattr(link_create_res, 'isError', True):
                        print(f"  FAILED to create linking note: {link_create_res}. Skipping backlink test.")
                    else:
                        print("  Linking note created.")
                        
                        # 2. Call get_backlinks (Only if linking note created)
                        print(f"Calling tool: {backlinks_tool} for target '{backlink_target}'")
                        try:
                            result = await session.call_tool(backlinks_tool, arguments={"note_path": backlink_target})
                            if result and not getattr(result, 'isError', True) and result.content:
                                import json
                                try:
                                    backlink_list = json.loads(getattr(result.content[0], 'text', '[]'))
                                    if isinstance(backlink_list, list):
                                        print(f"  Tool {backlinks_tool} successful. Found {len(backlink_list)} backlinks.")
                                        print(f"  Backlinks found: {backlink_list}")
                                        # Verification
                                        if linking_note in backlink_list:
                                            print("  Verification PASSED: Temporary linking note found in backlinks.")
                                        else:
                                            print("  Verification FAILED: Temporary linking note NOT found in backlinks.")
                                    else:
                                        # Correct f-string
                                        content_text = getattr(result.content[0], 'text', '')
                                        print(f"  Tool {backlinks_tool} FAILED: Result content was not a JSON list: {content_text}")
                                except json.JSONDecodeError:
                                     # Correct f-string
                                     content_text = getattr(result.content[0], 'text', '')
                                     print(f"  Tool {backlinks_tool} FAILED: Could not parse JSON backlink list: {content_text}")
                            else:
                                 print(f"Tool {backlinks_tool} FAILED: {result}")
                        except Exception as e:
                            print(f"Tool {backlinks_tool} FAILED with exception: {e}")
                            
                except Exception as create_link_e:
                    print(f"  FAILED to create linking note with exception: {create_link_e}. Skipping backlink test.")
                    
                # 3. Cleanup linking note (always attempt if path exists)
                if os.path.exists(linking_note_full):
                    print(f"  Cleaning up temporary linking note: {linking_note}")
                    try:
                        cleanup_args = {"relative_note_path": linking_note}
                        await session.call_tool("delete_note", arguments=cleanup_args)
                        print("  Linking note cleanup successful.")
                    except Exception as cleanup_e:
                         print(f"  WARNING: Failed to cleanup linking note '{linking_note}': {cleanup_e}")
                else:
                    print(f"  Skipping cleanup as linking note '{linking_note}' was not created or already gone.")

    except httpx.ConnectError as e:
        print(f"HTTPX ConnectError: Failed to connect to the server at {sse_endpoint_url}. Is it running?")
        print(f"  Details: {e}")
    except ConnectionRefusedError as e:
        print(f"ConnectionRefusedError: Connection was refused by the server at {sse_endpoint_url}. Is it running and accessible?")
        print(f"  Details: {e}")
    except Exception as e:
        # Catch other potential errors during connection or session
        print(f"An unexpected error occurred during the client test: {type(e).__name__}: {e}")
        # Optionally add traceback for more detail:
        # import traceback
        # traceback.print_exc()
    finally:
        # --- Cleanup Test File --- 
        print("\nRunning cleanup...")
        if os.path.exists(test_note_full_path):
            try:
                os.remove(test_note_full_path)
                print(f"Successfully deleted test file: {test_note_full_path}")
            except Exception as cleanup_error:
                print(f"Error deleting test file {test_note_full_path}: {cleanup_error}")
        else:
            print(f"Test file not found for cleanup: {test_note_full_path}")

if __name__ == "__main__":
    # Handle potential asyncio errors on Windows when exiting
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    asyncio.run(run_test()) 