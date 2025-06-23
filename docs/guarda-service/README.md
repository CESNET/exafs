# Guarda Service for ExaBGP
This is a systemd service designed to monitor ExaBGP and reapply commands after a restart or shutdown. The guarda.service runs on the host system and is triggered whenever the ExaBGP service restarts, thanks to the WantedBy configuration in systemd. After each restart, the Guarda service will reapply all valid and active rules to the ExaBGP rules table.

## Usage (as root)

First, set the environment variable with the correct URL for your installation. The announce_all endpoint is only accessible from localhost within the app, so ensure that your configuration includes the correct local IP address.

```bash
export GUARDA_URL=http://127.0.0.1:8080/rules/announce_all
cp guarda.service /usr/lib/systemd/system/guarda.service
systemctl start guarda.service
systemctl enable guarda.service
```
