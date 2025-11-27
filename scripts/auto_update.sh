#!/bin/bash
# Auto-update script: performs apt update/upgrade and cleanup, logs output, and emails report.
# Intended to run on Debian/Ubuntu hosts as root (e.g. a Droplet). If you run this inside a
# container, note that `apt` will update the container image, not the host.

LOGFILE="/var/log/auto_update.log"
EMAIL="gubbyagubbya@gmail.com"

set -o errexit
set -o pipefail
set -o nounset

timestamp() { date +"%Y-%m-%d %H:%M:%S"; }

# Ensure script is run as root
if [[ $(id -u) -ne 0 ]]; then
  echo "[$(timestamp)] This script must be run as root. Exiting." >&2
  exit 1
fi

mkdir -p "$(dirname "$LOGFILE")"
touch "$LOGFILE"
chown root:root "$LOGFILE" || true
chmod 0640 "$LOGFILE" || true

echo "[$(timestamp)] Starting daily update..." >> "$LOGFILE"

# Update package lists and upgrade
if command -v apt >/dev/null 2>&1; then
  apt update -y >> "$LOGFILE" 2>&1 || echo "[$(timestamp)] apt update failed" >> "$LOGFILE"
  apt upgrade -y >> "$LOGFILE" 2>&1 || echo "[$(timestamp)] apt upgrade failed" >> "$LOGFILE"
else
  echo "[$(timestamp)] apt not found on this system. Skipping package update." >> "$LOGFILE"
fi

echo "[$(timestamp)] Cleaning up..." >> "$LOGFILE"
if command -v apt >/dev/null 2>&1; then
  apt autoremove -y >> "$LOGFILE" 2>&1 || true
  apt autoclean -y >> "$LOGFILE" 2>&1 || true
fi

echo "[$(timestamp)] Update completed successfully." >> "$LOGFILE"

# Email the logfile if `mail` is available; otherwise just exit.
if command -v mail >/dev/null 2>&1; then
  mail -s "Daily Update Report - Helloworld staging Server" "$EMAIL" < "$LOGFILE" || echo "[$(timestamp)] Failed to send mail" >> "$LOGFILE"
else
  echo "[$(timestamp)] 'mail' not found; skipping email." >> "$LOGFILE"
fi

exit 0
