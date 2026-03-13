# Cloud Deployment Skill

## Description
Manages cloud VM setup, deployment, monitoring, and troubleshooting for the AI Employee cloud agent.

## Trigger Phrases
- "deploy to cloud"
- "cloud setup"
- "check cloud status"
- "troubleshoot cloud"

## Instructions

### Setup Cloud VM
1. Read `scripts/cloud_setup.sh` for the provisioning script
2. Guide the user through:
   - VM creation (Oracle Cloud Free Tier recommended)
   - Running `cloud_setup.sh` on the VM
   - Configuring `/etc/ai-employee/.env`
   - Copying credentials (token.json, client_secret)
   - Starting the systemd service

### Docker Deployment (Alternative)
1. Read `deploy/Dockerfile.cloud` and `deploy/docker-compose.yml`
2. Guide through:
   - Creating `.env.cloud` from template
   - Running `docker compose up -d`
   - Verifying health checks

### Monitoring
1. Check deployment mode: `python scripts/deploy_config.py`
2. Check vault sync status: `cat AI_Employee_Vault/Updates/sync_status_*.md`
3. View cloud logs: `journalctl -u ai-employee-cloud -f`
4. Check scheduler health: verify `Dashboard.md` deployment section

### Troubleshooting
- **Service won't start**: Check `/etc/ai-employee/.env`, verify Python path
- **Vault sync fails**: Verify `VAULT_GIT_REMOTE`, check SSH keys
- **Gmail not working**: Re-authenticate `token.json` on cloud
- **Odoo connection fails**: Verify `ODOO_URL` is HTTPS, check `ODOO_VERIFY_SSL`

## Files
- `scripts/cloud_setup.sh` — VM provisioning
- `deploy/Dockerfile.cloud` — Container image
- `deploy/docker-compose.yml` — Full stack compose
- `deploy/ai-employee-cloud.service` — Systemd unit
- `scripts/deploy_config.py` — Configuration module
