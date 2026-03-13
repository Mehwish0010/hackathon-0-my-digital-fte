#!/usr/bin/env bash
# =============================================================================
# AI Employee Cloud VM Setup Script
# =============================================================================
# Provisions an Oracle Cloud Free Tier VM (or any Ubuntu 22.04+ server)
# for running the AI Employee cloud agent 24/7.
#
# Prerequisites:
#   - Ubuntu 22.04+ VM with SSH access
#   - At least 1GB RAM, 10GB disk
#   - Domain pointed to VM IP (for HTTPS via Caddy)
#
# Usage:
#   scp scripts/cloud_setup.sh user@your-vm:~/
#   ssh user@your-vm
#   chmod +x cloud_setup.sh
#   sudo ./cloud_setup.sh
# =============================================================================

set -euo pipefail

echo "=== AI Employee Cloud Setup ==="

# 1. System updates
echo "[1/8] Updating system..."
apt-get update && apt-get upgrade -y

# 2. Install dependencies
echo "[2/8] Installing dependencies..."
apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    git curl wget \
    chromium-browser \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 libpango-1.0-0 \
    libcairo2 libasound2

# 3. Create service user
echo "[3/8] Creating service user..."
useradd -r -m -d /opt/ai-employee -s /bin/bash ai-employee || true

# 4. Clone project
echo "[4/8] Cloning project..."
cd /opt/ai-employee
if [ ! -d ".git" ]; then
    sudo -u ai-employee git clone https://github.com/Mehwish0010/hackathon-0-my-digital-fte.git .
fi

# 5. Set up Python environment
echo "[5/8] Setting up Python environment..."
sudo -u ai-employee python3.11 -m venv .venv
sudo -u ai-employee .venv/bin/pip install --upgrade pip
sudo -u ai-employee .venv/bin/pip install schedule watchdog python-dotenv mcp \
    google-auth-oauthlib google-api-python-client playwright

# 6. Install Playwright browsers
echo "[6/8] Installing Playwright browsers..."
sudo -u ai-employee .venv/bin/python -m playwright install chromium

# 7. Clone vault repo (separate)
echo "[7/8] Setting up vault..."
if [ -n "${VAULT_GIT_REMOTE:-}" ]; then
    sudo -u ai-employee git clone "$VAULT_GIT_REMOTE" /opt/ai-employee/vault
else
    sudo -u ai-employee mkdir -p /opt/ai-employee/vault
    echo "NOTE: Set VAULT_GIT_REMOTE and re-run to enable vault sync"
fi

# 8. Set up environment and systemd
echo "[8/8] Configuring systemd service..."
mkdir -p /etc/ai-employee
if [ ! -f /etc/ai-employee/.env ]; then
    cat > /etc/ai-employee/.env << 'ENVEOF'
DEPLOYMENT_MODE=cloud
VAULT_PATH=/opt/ai-employee/vault
CLOUD_AGENT_ID=cloud
# VAULT_GIT_REMOTE=git@github.com:youruser/ai-employee-vault.git
# GMAIL credentials — copy token.json and client_secret to /opt/ai-employee/
DRY_RUN=false
ENVEOF
    chmod 600 /etc/ai-employee/.env
fi

# Copy systemd service
cp /opt/ai-employee/deploy/ai-employee-cloud.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable ai-employee-cloud

echo ""
echo "=== Setup Complete ==="
echo ""
echo "Next steps:"
echo "  1. Edit /etc/ai-employee/.env with your credentials"
echo "  2. Copy token.json and client_secret_*.json to /opt/ai-employee/"
echo "  3. Start the service: sudo systemctl start ai-employee-cloud"
echo "  4. Check status: sudo systemctl status ai-employee-cloud"
echo "  5. View logs: sudo journalctl -u ai-employee-cloud -f"
echo ""
echo "For Docker deployment instead:"
echo "  cd /opt/ai-employee/deploy"
echo "  cp .env.cloud.example .env.cloud"
echo "  docker compose up -d"
