import argparse
import asyncio
import json
import logging
import os
import re
from xmlrpc import client

from dotenv import load_dotenv
from eunomia_mcp import create_eunomia_middleware
from fastmcp import FastMCP, Client
from fastmcp.server.auth import OAuthProvider
from fastmcp.server.auth.providers.google import GoogleProvider
from fastmcp.server.auth.providers.jwt import JWTVerifier, StaticTokenVerifier
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from pprint import pformat

# Load environment variables from .env file
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("mcp_proxy")
logger.setLevel(logging.INFO)

logger.info("Starting MCP proxy server...")


def load_proxy_config():
    """Load server configuration from a JSON file with environment variable interpolation.

    The file path is determined by the MCP_PROXY_SERVERS_CONFIG environment variable,
    which defaults to 'servers.json' in the module's root directory.

    Environment variables in the format ${ENV_VARIABLE} will be replaced with their
    values if they exist, otherwise they will be left unchanged.
    """
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Get config file path from environment variable or use default
    config_file = os.getenv(
        "MCP_PROXY_SERVERS_CONFIG", os.path.join(script_dir, "servers.json")
    )

    def interpolate_env_vars(text):
        """Replace ${ENV_VAR} patterns with environment variable values if they exist."""

        def replace_var(match):
            var_name = match.group(1)
            env_value = os.getenv(var_name)
            if env_value is not None:
                return env_value
            else:
                # Return the original placeholder if env var doesn't exist
                return match.group(0)

        return re.sub(r"\$\{([^}]+)\}", replace_var, text)

    logger.info(f"Loading proxy configuration from: {config_file}")
    try:
        with open(config_file, "r") as f:
            # Read the raw content and perform environment variable interpolation
            raw_content = f.read()
            interpolated_content = interpolate_env_vars(raw_content)

            # Parse the interpolated JSON
            config = json.loads(interpolated_content)
            logger.info(f"Loaded proxy configuration from: {config_file}")
            logger.info(f"Proxy configuration: {pformat(config)}")
            return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_file}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in configuration file {config_file}: {e}")
        raise


# Load server configuration from a JSON file
proxy_config = load_proxy_config()


def init_client():
    # Local Python script
    client = Client(proxy_config)

    async def client_main():
        async with client:
            # Basic server interaction
            await client.ping()

            # List available operations
            tools = await client.list_tools()
            resources = await client.list_resources()
            prompts = await client.list_prompts()

            tool_names = [tool.name for tool in tools]
            resource_names = [resource.name for resource in resources]
            prompt_names = [prompt.name for prompt in prompts]

            print("Available tools:", pformat(tool_names))
            print("Available resources:", pformat(resource_names))
            print("Available prompts:", pformat(prompt_names))
            await client.close()

    asyncio.run(client_main())


init_client()


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
    logger.info(f"Starting proxy with {transport} transport...")

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
