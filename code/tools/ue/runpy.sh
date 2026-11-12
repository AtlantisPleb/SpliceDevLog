#!/bin/zsh
# Run a Python file inside the open editor via its MCP server.
D=${0:a:h}
ARGS=$(python3 -c 'import json,sys; print(json.dumps({"toolset_name":"editor_toolset.toolsets.python_scripting.PythonScriptingTools","tool_name":"execute_python","arguments":{"script":{"content":open(sys.argv[1]).read(),"language":"Python"}}}))' "$1")
python3 $D/mcp.py call_tool "$ARGS"
