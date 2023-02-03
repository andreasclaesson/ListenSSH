# ListenSSH
Easily report all connection attempts on common vulnerable ports to AbuseIPDB
<br>Reuploaded with permission from old owner (friend).

## Features
- AbuseIPDB reporter (with built-in ratelimits)
- Discord Webhooks (text or embed)
- IP-API integration on Discord embed webhooks


## Installation
<b>This guide requires basic Linux understanding.</b> Tools to install (install command below):
- [Python 3](https://www.python.org/downloads/)
- [Git](https://git-scm.com/downloads)


```sh
# Install required packages
apt install -y python3 python3-pip git

# Clone repository files
git clone https://github.com/andreasclaesson/ListenSSH
cd ListenSSH

# Install required python packages
pip install -r requirements.txt

# Move config file
mv config_example.ini config.ini

# Edit the config file (you may use your favorite text editor)
nano config.ini

# Start the script
python3 main.py
```

## Run in background

### Systemd
If you wish to run ListenSSH using Systemd, which we highly recommend, follow these instructions

```sh
cp systemd/listenssh.service /etc/systemd/system/listenssh.service

# Change the "WorkingDirectory" to the one where you have installed ListenSSH (unless its the root directory)
nano /etc/systemd/system/listenssh.service

systemctl daemon-reload
systemctl enable listenssh.service
systemctl start listenssh.service
```

### PM2
```sh
# Make it so PM2 restarts ListenSSH on server reboot
pm2 startup

# Start ListenSSH
pm2 start

# Save ListenSSH to PM2 so it will be restarted on reboot.
pm2 save
```