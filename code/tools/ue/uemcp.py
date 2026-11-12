"""Small client for the Unreal editor's MCP server (127.0.0.1:8000).

    from uemcp import tool, py
    tool("BlueprintToolsets.BlueprintDslToolset.Write", assetPath=..., dsl=...)
    py("unreal.log('hi')\\n'ok'")   # run Python inside the editor, return its last value
"""
import json
import urllib.request

URL = "http://127.0.0.1:8000/mcp"
_sid = None


def _post(body):
    global _sid
    h = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    if _sid:
        h["Mcp-Session-Id"] = _sid
    r = urllib.request.urlopen(urllib.request.Request(URL, json.dumps(body).encode(), h), timeout=600)
    _sid = r.headers.get("Mcp-Session-Id") or _sid
    txt = r.read().decode()
    return json.loads(txt) if txt.strip() else None


def _init():
    if _sid:
        return
    _post({"jsonrpc": "2.0", "id": 1, "method": "initialize",
           "params": {"protocolVersion": "2025-06-18", "capabilities": {},
                      "clientInfo": {"name": "uemcp", "version": "1"}}})
    _post({"jsonrpc": "2.0", "method": "notifications/initialized"})


class ToolError(RuntimeError):
    pass


def tool(full_name, **arguments):
    """Call Toolset.Tool (full dotted name). Returns parsed JSON or text.

    If the editor is busy with a slow task (saving, compiling shaders), it refuses tool
    calls without making changes; wait and retry for up to 5 minutes.
    """
    import time
    for attempt in range(60):
        try:
            return _tool_once(full_name, **arguments)
        except ToolError as e:
            if "running a slow task" not in str(e) or attempt == 59:
                raise
            time.sleep(5)


def _tool_once(full_name, **arguments):
    _init()
    toolset, name = full_name.rsplit(".", 1)
    d = _post({"jsonrpc": "2.0", "id": 2, "method": "tools/call",
               "params": {"name": "call_tool",
                          "arguments": {"toolset_name": toolset, "tool_name": name, "arguments": arguments}}})
    if "error" in d:
        raise ToolError(json.dumps(d["error"]))
    res = d.get("result", {})
    text = "\n".join(c.get("text", "") for c in res.get("content", []))
    if res.get("isError"):
        raise ToolError(text)
    try:
        return json.loads(text)
    except ValueError:
        return text


def py(source):
    """Run Python in the editor; returns the script's final expression value."""
    r = tool("editor_toolset.toolsets.python_scripting.PythonScriptingTools.execute_python",
             script={"content": source, "language": "Python"})
    return r.get("returnValue") if isinstance(r, dict) else r


def ref(path):
    return {"refPath": path}
