#!/bin/bash
# First-boot setup for the Oracle A1 VM (Ubuntu 24.04 aarch64).
# Paste into Create Instance → Show advanced options → Management → "Paste cloud-init script".
# Safe to re-run by hand: sudo bash cloud-init.sh   (log: /var/log/cloud-init-output.log)
set -euo pipefail

# --- SSH: keys only, no root login ---
# 00- so it's read before Ubuntu's 50-cloud-init.conf; sshd keeps the first value it sees.
cat > /etc/ssh/sshd_config.d/00-hardening.conf <<'CONF'
PasswordAuthentication no
KbdInteractiveAuthentication no
PermitRootLogin no
CONF
sshd -t
systemctl reload ssh

# --- Docker Engine + compose plugin from Docker's apt repo (not snap) ---
apt-get update
apt-get install -y ca-certificates curl
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
cat > /etc/apt/sources.list.d/docker.sources <<CONF
Types: deb
URIs: https://download.docker.com/linux/ubuntu
Suites: $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}")
Components: stable
Signed-By: /etc/apt/keyrings/docker.asc
CONF
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Lets the default user run docker without sudo (docker group = root-equivalent; single-admin VM).
usermod -aG docker ubuntu
