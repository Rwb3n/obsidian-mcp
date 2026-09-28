import json
import os
import subprocess
import sys


def test_stdio_initialize_handshake(tmp_path):
    request = {
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {"protocolVersion": "2024-11-05", "capabilities": {}, "clientInfo": {"name": "t", "version": "1"}},
    }
    env = {k: v for k, v in os.environ.items() if not k.startswith("OMCP_")}
    env.update({"OMCP_VAULT_PATH": str(tmp_path), "PYTHONUNBUFFERED": "1"})
    proc = subprocess.Popen(
        [sys.executable, "-m", "obsidian_mcp_server.main"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, text=True,
    )
    try:
        proc.stdin.write(json.dumps(request) + "\n")
        proc.stdin.flush()
        line = proc.stdout.readline()  # stdout must carry only protocol messages
    finally:
        proc.kill()
        proc.communicate(timeout=10)
    response = json.loads(line)
    assert response["id"] == 1
    assert response["result"]["serverInfo"]["name"] == "Obsidian Vault Access"
