#!/bin/bash
# On the Micro, from the copied infra/ dir:  sudo bash install-a1-runner.sh
set -euo pipefail
cd "$(dirname "$0")"

apt-get update -qq
apt-get install -y python3-venv
install -d /opt/a1-runner
install -m 644 a1_runner.py cloud-init.sh /opt/a1-runner/
[ -x /opt/a1-runner/venv/bin/python ] || python3 -m venv /opt/a1-runner/venv
/opt/a1-runner/venv/bin/pip install -q --upgrade oci
install -m 644 a1-runner.service /etc/systemd/system/
systemctl daemon-reload

[ -f /etc/a1-runner.env ] || install -m 600 a1-runner.env.example /etc/a1-runner.env
echo "Next: fill TOPIC_OCID in /etc/a1-runner.env, then: sudo systemctl enable --now a1-runner"
