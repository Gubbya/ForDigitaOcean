# Auto Update - Host Cron Installation

This document shows the exact commands to install the host cron job for `scripts/auto_update.sh`.

These commands are intended to run on the target Debian/Ubuntu host (for example a DigitalOcean Droplet).
Run them as root or with `sudo`.

1) Make the script executable and move it to `/usr/local/bin`:

```bash
sudo mv /path/to/repo/scripts/auto_update.sh /usr/local/bin/auto_update.sh
sudo chmod 750 /usr/local/bin/auto_update.sh
sudo chown root:root /usr/local/bin/auto_update.sh
```

Replace `/path/to/repo` with where you placed this repository on the host.

2) Install the cron file into `/etc/cron.d` (this file contains the user field):

```bash
sudo cp /path/to/repo/scripts/auto_update.cron /etc/cron.d/auto_update
sudo chmod 644 /etc/cron.d/auto_update
```

3) Install the logrotate rule so logs don't grow indefinitely:

```bash
sudo cp /path/to/repo/scripts/logrotate/auto_update /etc/logrotate.d/auto_update
sudo chmod 644 /etc/logrotate.d/auto_update
```

4) (Optional) Install mail support so the script can email the report. On Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y mailutils
```

If you prefer to send mail through an external SMTP server, configure an MTA or use `msmtp` and update the system-wide config.

5) Test the script manually (recommended):

```bash
sudo /usr/local/bin/auto_update.sh
```

6) Verify cron is scheduled (validate `cron.d` file is readable by `cron`):

```bash
sudo systemctl status cron
sudo tail -n 200 /var/log/auto_update.log
```

Notes
- The script runs `apt` commands and must be executed on the host (Droplet) as root. Running inside a container will only update packages inside that container.
- If you want email reports but `mailutils` is not desirable, I can update the script to post logs to an HTTP endpoint or to send via SMTP client.
