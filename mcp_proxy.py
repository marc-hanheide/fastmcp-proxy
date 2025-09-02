import argparse
import os
from dotenv import load_dotenv
from fastmcp import FastMCP
from fastmcp.server.auth.providers.jwt import JWTVerifier, StaticTokenVerifier
from fastmcp.server.auth import OAuthProvider
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from eunomia_mcp import create_eunomia_middleware
from fastmcp.server.auth.providers.google import GoogleProvider

# Load environment variables from .env file
load_dotenv()

# Get OIDC configuration from environment variables
OIDC_CLIENT_ID = os.getenv("OIDC_CLIENT_ID")
OIDC_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET")
OIDC_ISSUER = os.getenv("OIDC_ISSUER")
ZROK_NAME = os.getenv("ZROK_NAME")

# Load server configuration from a JSON file
proxy_config = {
    "mcpServers": {
        "context7": {
            "transport": "stdio",
            "command": "npx",
            "args": ["-y", "@upstash/context7-mcp"],
        },
        "time": {
            "transport": "stdio",
            "command": "uvx",
            "args": ["mcp-server-time", "--local-timezone", "Etc/UTC"],
        },
        "mapbox": {
            "timeout": 60,
            "command": "npx",
            "args": ["-y", "@mapbox/mcp-server"],
        },
    }
}


# Create a FastMCP application instance that acts as a proxy
app = FastMCP.as_proxy(proxy_config, name="Google-authenticated MCP proxy")
# Add middleware to your server
middleware = create_eunomia_middleware(policy_file="mcp_policies.json")
app.add_middleware(middleware)


@app.tool
def echo_tool(text: str) -> str:
    """Echo the input text"""
    return text


@app.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")


def main(transport="http", port=8000, host="127.0.0.1"):
    print(f"Starting proxy with {transport} transport...")
    
    # Update the OAuth provider base URL if using OAuthProvider
    if OIDC_CLIENT_ID and OIDC_CLIENT_SECRET and OIDC_ISSUER:
        # Update the base URL in the OAuth provider to match actual server configuration
        if hasattr(auth, 'base_url'):
            if host == "0.0.0.0":
                # When binding to all interfaces, use localhost for OAuth redirects
                new_base_url = f"http://localhost:{port}"
            else:
                new_base_url = f"http://{host}:{port}"
            
            # Update the base URL in the OAuth provider
            auth.base_url = new_base_url
            print(f"OAuth provider configured with base URL: {new_base_url}")

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
    subparsers = parser.add_subparsers(
        dest="transport", required=True, help="Transport protocol to use"
    )

    # Stdio transport
    parser_stdio = subparsers.add_parser("stdio", help="Run with stdio transport")

    # SSE (Server-Sent Events) transport
    parser_sse = subparsers.add_parser("sse", help="Run with SSE transport")
    parser_sse.add_argument(
        "--port", type=int, default=8000, help="Port to run the SSE server on"
    )
    parser_sse.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host to bind the SSE server to"
    )

    # Streamable HTTP transport
    parser_http = subparsers.add_parser(
        "http", help="Run with Streamable HTTP transport"
    )
    parser_http.add_argument(
        "--port", type=int, default=8001, help="Port to run the HTTP server on"
    )
    parser_http.add_argument(
        "--host", type=str, default="127.0.0.1", help="Host to bind the HTTP server to"
    )

    args = parser.parse_args()

    main(transport=args.transport, port=args.port, host=args.host)
