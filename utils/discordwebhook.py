import configparser
import logging

import requests

logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=logging.INFO)

config = configparser.ConfigParser()
config.read('config.ini')

try:
  message_type = config['Discord']['Type']
except:
  logging.warn('Discord.Type is missing from config! Throwback value: "embed". Please check example config.')
  message_type = 'embed'

def discord_webhook(address, port, webhook_url, servername, ip_data):
  message = {}
  fields = []

  if message_type == 'message' or not message_type :
    message = {
        "content": f'Unauthorized connection attempt detected from IP address {str(address)} to port {port} ({servername})',
    }
    
  fields.extend([
    {
      'name': 'IP Address',
      'value': str(address[0])
    },
    {
      'name': 'Attacked port',
      'value': int(port)
    }
  ])

  if ip_data:
    fields.extend([ 
      {
        'name': 'ISP',
        'value': ip_data.get('isp'),
        'inline': True
      },
      {
        'name': 'Country',
        'value': ip_data.get('country'),
        'inline': True
      }
    ])

  if message_type == 'embed':
    message["embeds"] = [
      {
        "title" : "Unauthorized connection attempt",
        "color": "15158332",
        "description" : f'Unauthorized connection attempt detected from IP address {str(address[0])} to port {port}',
        "fields": fields,
        "footer": {
          'text': f'Server: {servername}'
        }

      }
    ]

  response = requests.post(webhook_url, json=message)

  if response.status_code == 429:
    logging.warn('Ratelimited from sending webhooks')
