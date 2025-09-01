
import asyncio
import argparse
import json
from fastmcp import FastMCP, Client
from fastmcp.server.proxy import ProxyClient
from starlette.requests import Request
from starlette.responses import PlainTextResponse


# Load server configuration from a JSON file

proxy_config = {
  "mcpServers": {
    "context7": {
      "transport": "stdio",
      "command": "npx",
      "args": ["-y", "@upstash/context7-mcp"]
    },
    "time": {
      "transport": "stdio",
      "command": "uvx",
      "args": ["mcp-server-time", "--local-timezone", "Etc/UTC"]
    },
    "mapbox": {
      "timeout": 60,
      "command": "npx",
      "args": [ "-y", "@mapbox/mcp-server"]
    }

  }
}

from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import StaticTokenVerifier

# Define development tokens and their associated claims
verifier = StaticTokenVerifier(
    tokens={
        "testtoken": {
            "client_id": "marc@hanheide,net",
            "scopes": ["read:data", "write:data", "admin:users"]
        }
    },
    required_scopes=["read:data"]
)

#mcp = FastMCP(name="Development Server", auth=verifier)


# Create a FastMCP application instance that acts as a proxy
# FastMCP.as_proxy() handles the internal creation and mounting of clients

app = FastMCP.as_proxy(proxy_config, name="proxy", auth=verifier)
# named_proxies = FastMCP.as_proxy(backend=proxy_client)
# app.mount(named_proxies, prefix="/proxies", as_proxy=True)


@app.tool
def echo_tool(text: str) -> str:
    """Echo the input text"""
    return text


@app.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


def main(transport="http", port=8000, host="127.0.0.1"):


    print(f"Starting proxy with {transport} transport...")

    if transport == "stdio":
        # Run the server over standard input/output
        app.run(transport="stdio")
    elif transport == "sse":
        # Run the server with Server-Sent Events
        app.run(transport="sse", port=port, host=host)
    elif transport == "http":
        # Run the server with streamable HTTP
        app.run(transport="http", port=port, host=host)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the FastMCP proxy server.")
    subparsers = parser.add_subparsers(dest="transport", required=True, help="Transport protocol to use")

    # Stdio transport
    parser_stdio = subparsers.add_parser("stdio", help="Run with stdio transport")

    # SSE (Server-Sent Events) transport
    parser_sse = subparsers.add_parser("sse", help="Run with SSE transport")
    parser_sse.add_argument("--port", type=int, default=8000, help="Port to run the SSE server on")
    parser_sse.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the SSE server to")

    # Streamable HTTP transport
    parser_http = subparsers.add_parser("http", help="Run with Streamable HTTP transport")
    parser_http.add_argument("--port", type=int, default=8001, help="Port to run the HTTP server on")
    parser_http.add_argument("--host", type=str, default="127.0.0.1", help="Host to bind the HTTP server to")

    args = parser.parse_args()

    main(transport=args.transport, port=args.port, host=args.host)