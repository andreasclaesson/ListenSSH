# ListenSSH
Easily report all connection attempts on common vulnerable ports to AbuseIPDB

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

### Docker
Docker support is intended for Linux hosts.

```sh
# Create your config first
cp config_example.ini config.ini
nano config.ini

# Build and start in the background
docker compose up -d

# Follow the logs
docker compose logs -f
```

Rebuild after changing the code with `docker compose up -d --build`.

> **Note:** The container uses host networking (`network_mode: host`) so it binds the real ports
> and sees the real source IPs of connection attempts. On Docker's default bridge network the
> source address can be rewritten by NAT, which would report the wrong IP to AbuseIPDB.
> Host networking is Linux-only.

## License
Released under the [MIT License](LICENSE). You are free to use, copy, modify, merge, publish,
distribute, sublicense, and sell copies of this software.