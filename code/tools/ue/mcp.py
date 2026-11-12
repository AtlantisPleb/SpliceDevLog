"""Tiny client for the editor's unreal-mcp server. Usage: mcp.py METHOD_JSON_ARGS"""
import json, sys, urllib.request
URL = "http://127.0.0.1:8000/mcp"
def post(body, sid=None):
    data = json.dumps(body).encode()
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if sid: h["Mcp-Session-Id"] = sid
    r = urllib.request.urlopen(urllib.request.Request(URL, data=data, headers=h), timeout=120)
    return r.headers.get("Mcp-Session-Id"), r.read().decode()
sid, _ = post({"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-06-18","capabilities":{},"clientInfo":{"name":"c","version":"1"}}})
post({"jsonrpc":"2.0","method":"notifications/initialized"}, sid)
name = sys.argv[1]; args = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
_, out = post({"jsonrpc":"2.0","id":2,"method":"tools/call","params":{"name":name,"arguments":args}}, sid)
try:
    d = json.loads(out)
    for c in d.get("result", {}).get("content", []):
        print(c.get("text", c))
    if "error" in d: print("ERROR", d["error"])
except Exception:
    print(out)
