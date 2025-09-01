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

The proxy implements OIDC authentication compatible with Claude's remote MCP server requirements using FastMCP's `OAuthProvider`:

- **Provider**: Keycloak server at `https://lcas.lincoln.ac.uk/auth/realms/Marc`
- **Client Configuration**: Uses pre-configured client credentials (`mcp` client)
- **OAuth2 Flow**: Standard authorization code flow with PKCE support
- **Token Verification**: JWT verification using JWKS endpoint
- **Automatic Endpoints**: OAuth2 discovery and authorization endpoints auto-generated

### OAuth2 Endpoints

The proxy automatically provides these OAuth2 endpoints:
- `/.well-known/oauth-authorization-server` - OAuth2 server metadata
- `/authorize` - Authorization endpoint for OAuth2 flow
- `/token` - Token exchange endpoint
- `/.well-known/oauth-protected-resource` - Resource server metadata

### Environment Configuration

Required OIDC environment variables in `.env`:
```bash
OIDC_CLIENT_ID=mcp                                                    # Pre-configured client ID
OIDC_CLIENT_SECRET=yKcQDTpgHBzdQtsZn6eHMK5MY5ffZzlR                  # Client secret from Keycloak
OIDC_ISSUER=https://lcas.lincoln.ac.uk/auth/realms/Marc              # Keycloak realm issuer
```

### Authentication Flow for Claude

1. **Discovery**: Claude queries `/.well-known/oauth-authorization-server` for OAuth2 configuration
2. **Authorization**: Claude redirects user to `/authorize` endpoint with client credentials
3. **User Login**: User authenticates with Keycloak and grants authorization
4. **Code Exchange**: Claude exchanges authorization code for access token at `/token` endpoint
5. **API Access**: Claude uses Bearer token to access MCP endpoints
6. **Token Validation**: Server validates token against Keycloak JWKS endpoint

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

### OAuth2 Authorization Code Flow
1. Claude discovers OAuth2 configuration from server metadata endpoints
2. Claude initiates authorization flow by redirecting to Keycloak
3. User authenticates with Keycloak and grants access to the MCP client
4. Claude receives authorization code and exchanges it for access token
5. Claude uses Bearer token to access MCP tools and resources

### Server Endpoints
- **MCP Endpoint**: `/mcp` - Main MCP protocol endpoint (requires Bearer token)
- **Health Check**: `/health` - Health status (no auth required)
- **OAuth Discovery**: `/.well-known/oauth-authorization-server` - OAuth2 server metadata
- **Authorization**: `/authorize` - OAuth2 authorization endpoint
- **Token Exchange**: `/token` - OAuth2 token endpoint
- **Resource Info**: `/.well-known/oauth-protected-resource` - Resource server metadata

### Token Requirements
- **Algorithm**: RS256 (RSA with SHA-256)
- **Issuer**: Must match configured `OIDC_ISSUER`
- **Audience**: Any valid audience (flexible for Keycloak integration)
- **Minimum Scope**: `openid` (additional scopes configurable per server)

### Keycloak Integration
- **Realm**: `Marc` at `https://lcas.lincoln.ac.uk/auth/realms/Marc`
- **Client Type**: Confidential client with authorization code flow
- **Valid Redirect URIs**: Must include Claude's callback URLs
- **Client Authentication**: Client secret authentication
- **Supported Flows**: Authorization code flow with PKCE

## Container Architecture

Uses `ghcr.io/astral-sh/uv:python3.12-alpine` base image with:
- Pre-installed uv for fast Python package management
- Node.js/npm for mixed server ecosystem support
- Non-root execution for security
- Multi-transport port exposure (8000, 8001)
- Environment-based OIDC configuration