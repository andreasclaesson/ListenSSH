import datetime
import logging
import os
import select
import signal
import socket
import sys

import requests
from cachetools import TTLCache

from utils.config import ConfigError, load_config, validate_config
from utils.discordwebhook import discord_webhook
from utils.ip_api import ip_api

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

# Resolve config.ini next to this script so it works regardless of the CWD.
CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.ini')
REQUEST_TIMEOUT = 5
# AbuseIPDB only accepts one report per IP every 15 minutes, so cache for that window.
REPORT_CACHE_TTL = 900

try:
  settings = validate_config(load_config(CONFIG_FILE))
except ConfigError as e:
  raise SystemExit(str(e))

api_key = settings['api_key']
url = settings['report_url']
categories = settings['categories']
discord_webhook_url = settings['discord_webhook_url']
discord_message_type = settings['discord_message_type']
servername = settings['servername']
ports = settings['ports']
ip_api_enabled = settings['ip_api_enabled']

cache = TTLCache(maxsize=1024, ttl=REPORT_CACHE_TTL)

servers = []

for port in ports:
  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

  try:
    server.bind(('0.0.0.0', port))
    server.listen(5)
    servers.append(server)
  except OSError as e:
    logging.warning(f'Failed to bind port {port} ({e}). Port is perhaps in use?')
    server.close()

if not servers:
  raise SystemExit('Could not bind to any port, nothing to listen on. Exiting.')


def shutdown(*_args):
  logging.info('Shutting down ListenSSH...')
  for server in servers:
    server.close()
  sys.exit(0)


signal.signal(signal.SIGINT, shutdown)
signal.signal(signal.SIGTERM, shutdown)

logging.info(f'ListenSSH is running, listening on {len(servers)} port(s)')


def report_ip(address, port):
  """Report a connection attempt to AbuseIPDB. Never raises."""
  ip = str(address[0])

  if cache.get(ip):
    logging.info(f'{ip} was reported within the last {REPORT_CACHE_TTL}s, skipping AbuseIPDB report.')
    return

  params = {
      'ip': ip,
      'categories': categories,
      'comment': f'Unauthorized connection attempt detected from IP address {ip} to port {port} ({servername})',
      'timestamp': datetime.datetime.now(datetime.timezone.utc).isoformat(),
  }

  headers = {
      'Accept': 'application/json',
      'Key': api_key,
  }

  try:
    response = requests.post(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
  except requests.RequestException as e:
    logging.warning(f'Failed to report {ip} to AbuseIPDB: {e}')
    return

  if response.status_code == 200:
    cache[ip] = True
    logging.info(f'Reported {ip} to AbuseIPDB.')
  elif response.status_code == 429:
    # Per-IP cooldown or daily limit; back off to avoid hammering the API.
    cache[ip] = True
    retry_after = response.headers.get('Retry-After')
    logging.warning(f'AbuseIPDB rate limited while reporting {ip}'
                    + (f', retry after {retry_after}s.' if retry_after else '.'))
  else:
    # Unexpected failure: do not cache so the next attempt is reported again.
    logging.warning(f'AbuseIPDB report for {ip} failed with status '
                    f'{response.status_code}: {response.text[:200]}')


def handle_connection(connection, address, port):
  if ip_api_enabled:
    ip_data = ip_api(address[0])
    logging.info(f'[CONNECTION ATTEMPT] IP={address[0]} SRC_PORT={address[1]} '
                 f'DEST_PORT={port} ISP="{ip_data.get("isp") if ip_data else None}" '
                 f'COUNTRY={ip_data.get("country") if ip_data else None}')
  else:
    ip_data = None
    logging.info(f'[CONNECTION ATTEMPT] IP={address[0]} SRC_PORT={address[1]} DEST_PORT={port}')

  if discord_webhook_url:
    discord_webhook(address, int(port), discord_webhook_url, servername, ip_data, discord_message_type)

  report_ip(address, int(port))


while True:
  ready_server = select.select(servers, [], [])[0][0]

  try:
    connection, address = ready_server.accept()  # address is the ip
  except OSError as e:
    logging.warning(f'Failed to accept a connection: {e}')
    continue

  port = ready_server.getsockname()[1]

  try:
    handle_connection(connection, address, port)
  except Exception:
    logging.exception('Unexpected error while handling connection')
  finally:
    connection.close()
