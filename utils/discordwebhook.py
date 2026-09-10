import logging

import requests

REQUEST_TIMEOUT = 5


def _format_ip(address):
  """Return just the IP from the (host, port) tuple produced by socket.accept()."""
  if isinstance(address, (tuple, list)):
    return str(address[0])
  return str(address)


def discord_webhook(address, port, webhook_url, servername, ip_data, message_type='embed'):
  """Send a connection-attempt notification to Discord. Never raises."""
  ip = _format_ip(address)
  message = {}

  if message_type == 'message' or not message_type:
    message['content'] = (f'Unauthorized connection attempt detected from IP address '
                          f'{ip} to port {port} ({servername})')

  if message_type == 'embed':
    fields = [
      {
        'name': 'IP Address',
        'value': ip,
      },
      {
        'name': 'Attacked port',
        'value': int(port),
      },
    ]

    if ip_data:
      fields.extend([
        {
          'name': 'ISP',
          'value': ip_data.get('isp') or 'Unknown',
          'inline': True,
        },
        {
          'name': 'Country',
          'value': ip_data.get('country') or 'Unknown',
          'inline': True,
        },
      ])

    message['embeds'] = [
      {
        'title': 'Unauthorized connection attempt',
        'color': 15158332,
        'description': f'Unauthorized connection attempt detected from IP address {ip} to port {port}',
        'fields': fields,
        'footer': {
          'text': f'Server: {servername}',
        },
      }
    ]

  if not message:
    logging.warning(f'Unknown Discord.Type "{message_type}", skipping webhook. Use "embed" or "message".')
    return

  try:
    response = requests.post(webhook_url, json=message, timeout=REQUEST_TIMEOUT)
  except requests.RequestException as e:
    logging.warning(f'Failed to send Discord webhook: {e}')
    return

  if response.status_code == 429:
    logging.warning('Ratelimited from sending webhooks.')
  elif response.status_code not in (200, 204):
    logging.warning(f'Discord webhook returned status {response.status_code}: {response.text[:200]}')
