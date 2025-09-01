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

### OpenID Connect (OIDC) Integration

The proxy implements OIDC authentication compatible with Claude's remote MCP server requirements:

- **Provider**: Keycloak server at `https://lcas.lincoln.ac.uk/auth/realms/Marc`
- **Client Configuration**: Uses pre-configured client credentials (not DCR)
- **Token Verification**: JWT verification using JWKS endpoint
- **Scope-based Authorization**: Each MCP server can require specific scopes

### Environment Configuration

Required OIDC environment variables in `.env`:
```bash
OIDC_CLIENT_ID=mcp                                                    # Pre-configured client ID
OIDC_CLIENT_SECRET=your_secret_here                                   # Client secret from Keycloak
OIDC_ISSUER=https://lcas.lincoln.ac.uk/auth/realms/Marc              # Keycloak realm issuer
```

### Scope Configuration

Each MCP server can require specific OAuth scopes:
- **context7**: Requires `context` scope for document search access
- **time**: Requires `time` scope for time operations
- **mapbox**: Requires `maps` scope for mapping services
- **Default**: Falls back to `openid` scope if no specific scope configured

### Development Fallback

If OIDC is not configured, the proxy falls back to static token authentication:
- Token: `testtoken`
- Scopes: `["openid", "context", "time", "maps"]`
- Client ID: `development`

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

### Authentication Flow
1. Claude requests access with OAuth2 Bearer token
2. Proxy verifies token against Keycloak JWKS endpoint
3. Token claims are validated (issuer, audience, signature)
4. User scopes are extracted from token
5. Access to MCP servers is granted based on required scopes

### Token Requirements
- **Algorithm**: RS256 (RSA with SHA-256)
- **Issuer**: Must match configured `OIDC_ISSUER`
- **Audience**: Must match configured `OIDC_CLIENT_ID`
- **Minimum Scope**: `openid` (additional scopes required per server)

### API Endpoints
- `/health`: Health check endpoint (no auth required)
- Standard MCP endpoints require valid Bearer token
- Tool access filtered by scope requirements

## Container Architecture

Uses `ghcr.io/astral-sh/uv:python3.12-alpine` base image with:
- Pre-installed uv for fast Python package management
- Node.js/npm for mixed server ecosystem support
- Non-root execution for security
- Multi-transport port exposure (8000, 8001)
- Environment-based OIDC configuration