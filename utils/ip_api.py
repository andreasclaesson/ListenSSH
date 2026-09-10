import logging

import requests
from cachetools import TTLCache

cache = TTLCache(maxsize=1024, ttl=900)

REQUEST_TIMEOUT = 5


def ip_api(ip):
  """Best-effort IP enrichment via ip-api.com. Returns None on failure."""
  cache_key = f'data_{ip}'
  cached = cache.get(cache_key)

  if cached is not None:
    return cached

  url = f'http://ip-api.com/json/{ip}?fields=status,message,country,isp,proxy,hosting'

  try:
    response = requests.get(url, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    ip_data = response.json()
  except requests.RequestException as e:
    logging.warning(f'Failed to fetch IP info for {ip}: {e}')
    return None
  except ValueError as e:
    logging.warning(f'Invalid IP info response for {ip}: {e}')
    return None

  if not isinstance(ip_data, dict) or ip_data.get('status') == 'fail':
    message = ip_data.get('message') if isinstance(ip_data, dict) else None
    logging.warning(f'ip-api.com could not resolve {ip}' + (f': {message}' if message else ''))
    return None

  cache[cache_key] = ip_data
  return ip_data
