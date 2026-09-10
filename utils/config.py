"""Loading and validation of config.ini.

Kept separate from main.py so the startup path stays short and every problem
with the config can be reported at once, before any sockets are opened.
"""
import configparser

DEFAULT_REPORT_URL = 'https://api.abuseipdb.com/api/v2/report'
DEFAULT_CATEGORIES = '18,20'
DEFAULT_DISCORD_TYPE = 'embed'

DISCORD_TYPES = ('embed', 'message')
TRUE_VALUES = ('yes', 'true', '1', 'on')
FALSE_VALUES = ('no', 'false', '0', 'off')

MIN_PORT = 1
MAX_PORT = 65535


class ConfigError(Exception):
  """Raised when config.ini is missing or contains invalid values."""

  def __init__(self, problems):
    if isinstance(problems, str):
      problems = [problems]
    self.problems = problems
    super().__init__('Invalid config.ini:\n  - ' + '\n  - '.join(problems))


def load_config(path):
  """Read config.ini from disk. Raises ConfigError if it can not be read."""
  # interpolation=None keeps '%' in values (e.g. a Server name) literal instead
  # of treating it as a configparser interpolation token.
  parser = configparser.ConfigParser(interpolation=None)
  if not parser.read(path):
    raise ConfigError(f'Config file was not found: {path}')
  return parser


def _get(parser, section, option, fallback=''):
  """Read an option without raising when the section or option is missing."""
  if not parser.has_section(section):
    return fallback
  return parser.get(section, option, fallback=fallback)


def _parse_bool(raw, fallback, label, problems):
  value = (raw or '').strip().lower()
  if not value:
    return fallback
  if value in TRUE_VALUES:
    return True
  if value in FALSE_VALUES:
    return False
  problems.append(f'{label} must be yes or no, got "{raw.strip()}".')
  return fallback


def _parse_ports(raw, problems):
  ports = []
  for entry in (raw or '').split(','):
    entry = entry.strip()
    if not entry:
      continue
    try:
      port = int(entry)
    except ValueError:
      problems.append(f'Ports contains a non-numeric value: "{entry}".')
      continue
    if not MIN_PORT <= port <= MAX_PORT:
      problems.append(f'Ports contains an out-of-range value: {port} (must be {MIN_PORT}-{MAX_PORT}).')
      continue
    if port not in ports:
      ports.append(port)
  return ports


def _parse_categories(raw, problems):
  value = (raw or '').strip() or DEFAULT_CATEGORIES
  categories = [c.strip() for c in value.split(',') if c.strip()]
  if not categories or not all(c.isdigit() for c in categories):
    problems.append(
      f'AbuseIPDB.Categories must be a comma-separated list of integers, got "{value}".'
    )
    return DEFAULT_CATEGORIES
  return ','.join(categories)


def validate_config(parser):
  """Validate a parsed config and return a dict of usable settings.

  Every problem is collected so the user can fix them all in one go instead of
  restarting once per mistake. Raises ConfigError if anything is wrong.
  """
  problems = []

  api_key = _get(parser, 'AbuseIPDB', 'Key').strip()
  if not api_key:
    problems.append(
      'Missing value for AbuseIPDB.Key (get a key at https://www.abuseipdb.com/account/api).'
    )

  report_url = _get(parser, 'AbuseIPDB', 'ReportURL', DEFAULT_REPORT_URL).strip() or DEFAULT_REPORT_URL
  if not report_url.startswith(('http://', 'https://')):
    problems.append(f'AbuseIPDB.ReportURL must start with http:// or https://, got "{report_url}".')

  categories = _parse_categories(_get(parser, 'AbuseIPDB', 'Categories'), problems)

  discord_webhook_url = _get(parser, 'Discord', 'WebhookURL').strip()
  if discord_webhook_url and not discord_webhook_url.startswith(('http://', 'https://')):
    problems.append(f'Discord.WebhookURL must start with http:// or https://, got "{discord_webhook_url}".')

  discord_message_type = _get(parser, 'Discord', 'Type', DEFAULT_DISCORD_TYPE).strip().lower() or DEFAULT_DISCORD_TYPE
  if discord_message_type not in DISCORD_TYPES:
    problems.append(f'Discord.Type must be one of {", ".join(DISCORD_TYPES)}, got "{discord_message_type}".')

  servername = _get(parser, 'Info', 'Server').strip()
  if not servername:
    problems.append('Missing value for Info.Server (used in reports and webhooks).')

  ports = _parse_ports(_get(parser, 'Ports', 'Ports'), problems)
  if not ports:
    problems.append('No valid ports configured in Ports.Ports.')

  ip_api_enabled = _parse_bool(_get(parser, 'IP_API', 'Enabled'), True, 'IP_API.Enabled', problems)

  if problems:
    raise ConfigError(problems)

  return {
    'api_key': api_key,
    'report_url': report_url,
    'categories': categories,
    'discord_webhook_url': discord_webhook_url,
    'discord_message_type': discord_message_type,
    'servername': servername,
    'ports': ports,
    'ip_api_enabled': ip_api_enabled,
  }
