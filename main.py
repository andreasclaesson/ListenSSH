import configparser
import logging
import random
import select
import signal
import socket
import string

import requests
from cachetools import TTLCache

from utils.discordwebhook import discord_webhook
from utils.ip_api import ip_api

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

config = configparser.ConfigParser()
config.read('config.ini')

try:
  with open('config.ini') as f:
    config.read(f)
except IOError:
    raise Exception('config.ini file was not found.')

if not config['AbuseIPDB']['Key']:
  raise Exception("Missing AbuseIPDB Key from config.ini, can not continue.")

url = config['AbuseIPDB']['ReportURL']
discord_webhook_url = config['Discord']['WebhookURL']
servername = config['Info']['Server']

try:
  ip_api_enabled = config['IP_API']['Enabled']
except:
  logging.warning('IP_API.Enabled is missing from config! Throwback value: "yes". Please check example config.')
  ip_api_enabled = "yes"

cache = TTLCache(maxsize=50, ttl=900)

servers = [] 

for port in config['Ports']['Ports'].split(","):
  ds = ("0.0.0.0", int(port))

  server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
  server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

  try:
    server.bind(ds)
    server.listen(1)
    
    servers.append(server)
  except:
    logging.warn(f'Failed to bind port {int(port)}. Port is perhaps in use?')


logging.info('ListenSSH is running')

while True:
  ready_server = select.select(servers, [], [])[0][0]

  connection, address = ready_server.accept()  # address is the ip
  port = ready_server.getsockname()[1]

  if ip_api_enabled == "yes":
    ip_data = ip_api(address[0])
    logging.info(f'[CONNECTION ATTEMPT] IP={str(address[0])} SRC_PORT={address[1]} DEST_PORT={port} ISP="{ip_data.get("isp")}" COUNTRY={ip_data.get("country")}')
  else: 
    ip_data = False
    logging.info(f'[CONNECTION ATTEMPT] IP={str(address[0])} SRC_PORT={address[1]} DEST_PORT={port}')
  
  if discord_webhook_url:
    discord_webhook(address, int(port), discord_webhook_url, servername, ip_data)

  params = {
      'ip': str(address[0]),
      'categories': config['AbuseIPDB']['Categories'],
      'comment': f"Unauthorized connection attempt detected from IP address {str(address[0])} to port {port} ({servername}) [{random.choice(string.ascii_letters)}]"
  }

  headers = {
      'Accept': 'application/json',
      'Key': config['AbuseIPDB']['Key']
  }


  if cache.get(str(address[0]), None) != True:
    response = requests.request(method='POST', url=url, params=params, headers=headers)

    if response.status_code == 429:
        cache[str(address[0])] = True
        
    else:
        cache[str(address[0])] = True
        pass

  connection.close()
