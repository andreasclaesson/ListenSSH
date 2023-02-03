import requests
from cachetools import TTLCache

cache = TTLCache(maxsize=50, ttl=900)

def ip_api(ip):
  url = f'http://ip-api.com/json/{ip}?fields=country,isp,proxy,hosting'
  cacheData = cache.get(f'data_{ip}', None)

  if cacheData:
    ip_data = cacheData
  else:
    response = requests.request(method='GET', url=url)

    cache[f'data_{ip}'] = response.json()
    ip_data = response.json()

  return ip_data
