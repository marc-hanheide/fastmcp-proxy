# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a FastMCP proxy server that exposes multiple MCP (Model Context Protocol) servers over various transport protocols. It's designed for production deployment using Docker containers with OpenID Connect (OIDC) authentication for Claude compatibility.

## Core Architecture

- **mcp_proxy.py**: Main FastMCP proxy application with OIDC authentication support
- **servers.json**: Configuration file defining which MCP servers to proxy (context7, fetch, time)
- **entrypoint.sh**: Docker entrypoint script that configures transport and networking based on environment variables
- **Dockerfile**: Production-ready Alpine Linux container with Python 3.12 and Node.js for mixed server support


## Authentication

### Google OAuth2 Integration

The proxy uses Google OAuth2 as the main authentication method, compatible with Claude and other MCP clients:

- **Provider**: Google OAuth2
- **Client Configuration**: Uses your own Google OAuth2 credentials
- **OAuth2 Flow**: Standard authorization code flow
- **Token Verification**: JWT verification using Google's public keys

### Environment Configuration

Set the following variables in your `.env` file (see `env.example`):
```bash
FASTMCP_SERVER_AUTH=GOOGLE
FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_ID=YOUR_GOOGLE_CLIENT_ID
FASTMCP_SERVER_AUTH_GOOGLE_CLIENT_SECRET=YOUR_GOOGLE_CLIENT_SECRET
FASTMCP_SERVER_AUTH_GOOGLE_BASE_URL=https://${ZROK_NAME}.zrok.lcas.group
FASTMCP_SERVER_AUTH_GOOGLE_REQUIRED_SCOPES=openid,https://www.googleapis.com/auth/userinfo.email
```

### Authentication Flow for Claude

1. Claude or the user is redirected to Google's OAuth2 login page
2. User authenticates with Google and grants access
3. The proxy receives the authorization code and exchanges it for an access token
4. Claude uses the Bearer token to access MCP endpoints
5. The proxy validates the token using Google's public keys

### Development Fallback

If Google OAuth2 is not configured, the proxy may fall back to static token authentication for development.

## Key Commands

### Docker Development
```bash
# Build and run with Docker Compose (recommended)
docker-compose up --build

# Build container manually
docker build -t mcp-proxy .

# Run with specific transport and OIDC
TRANSPORT=http PORT=8001 docker-compose up

# View logs
docker-compose logs -f
```

### Direct Python Execution
```bash
# Install dependencies (includes OIDC packages)
uv pip install -r requirements.txt

# Run with different transports
python mcp_proxy.py sse --host 0.0.0.0 --port 8000
python mcp_proxy.py http --host 0.0.0.0 --port 8001
python mcp_proxy.py stdio
```

## Configuration

### Environment Variables
- `TRANSPORT`: Protocol type (sse, http, stdio) - defaults to sse
- `HOST`: Bind address - defaults to 0.0.0.0
- `PORT`: Service port - defaults to 8000 for sse, 8001 for http
- `TZ`: Timezone - defaults to Etc/UTC
- `OIDC_CLIENT_ID`: OAuth2 client identifier
- `OIDC_CLIENT_SECRET`: OAuth2 client secret
- `OIDC_ISSUER`: OpenID Connect issuer URL

### MCP Server Configuration
Edit `servers.json` to add/modify MCP servers:
- **context7**: Node.js server via npx (document search) - requires `context` scope
- **fetch**: Python server via uvx (web content fetching) - requires `openid` scope
- **time**: Python server via uvx (time operations) - requires `time` scope
- **mapbox**: Node.js server via npx (mapping services) - requires `maps` scope

## Transport Protocols

The proxy supports three transport modes:
- **stdio**: Standard input/output for direct process communication
- **sse**: Server-Sent Events for web-based streaming
- **http**: Streamable HTTP for traditional web requests

## Dependencies

- **FastMCP 2.9.0+**: Core MCP proxy framework with auth support
- **python-jose**: JWT token verification
- **requests**: HTTP client for OIDC configuration
- **python-dotenv**: Environment variable loading
- **Node.js/npm**: Required for npx-based MCP servers
- **Python 3.12**: Runtime environment
- **uv**: Package management (containerized environment)

## Claude Integration

### OAuth2 Authorization Code Flow
1. Claude discovers OAuth2 configuration from server metadata endpoints
2. Claude initiates authorization flow by redirecting to Keycloak
3. User authenticates with Keycloak and grants access to the MCP client
4. Claude receives authorization code and exchanges it for access token
5. Claude uses Bearer token to access MCP tools and resources


### Server Endpoints
- **MCP Endpoint**: `/mcp` - Main MCP protocol endpoint (requires Bearer token)
- **Health Check**: `/health` - Health status (no auth required)


### Token Requirements
- **Algorithm**: RS256 (RSA with SHA-256)
- **Issuer**: Google
- **Audience**: Your configured client ID
- **Minimum Scope**: `openid` (additional scopes configurable per server)

## Container Architecture

Uses `ghcr.io/astral-sh/uv:python3.12-alpine` base image with:
- Pre-installed uv for fast Python package management
- Node.js/npm for mixed server ecosystem support
- Non-root execution for security
- Multi-transport port exposure (8000, 8001)
- Environment-based OIDC configuration