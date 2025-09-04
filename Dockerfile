# Use the official Astral uv image with Python 3.12 on Alpine
FROM ghcr.io/astral-sh/uv:python3.12-trixie AS base

# Install nodejs and npm for the npx command (runtime dependency for context7)
# Debian's package manager is apt
RUN apt-get update && apt-get install -y nodejs npm git

FROM base AS proxy_requirements

# Set the working directory
WORKDIR /app

# Copy requirements and install Python dependencies using the pre-installed uv
COPY requirements.txt servers.json /app/
RUN uv pip install --system --no-cache-dir -r requirements.txt


# preinsall some to make startup faster
RUN uvx --from git+https://github.com/marc-hanheide/microsoft-mcp python --version
RUN uvx --from mcp-server-time python --version
RUN npm install @mapbox/mcp-server


FROM proxy_requirements AS proxy

# Copy the rest of the application code
COPY . .

# Copy and set up entrypoint script
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

# Expose ports for both SSE (8000) and HTTP (8001) transports
EXPOSE 8000 8001

# Use entrypoint script to handle transport configuration
ENTRYPOINT ["/entrypoint.sh"]

FROM proxy AS mcps
# use this step to add more MCPs from source directly as needed
