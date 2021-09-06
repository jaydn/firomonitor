import json
import os

_CONFIG_FILE_PATH = os.path.expanduser('/config/config.json')

config = {
    "config_name": "config_name",
    "domain": "domain",
    "secret": "secret",
    "database_name": "database",
    "database_kvargs": {
        "user": "username",
        "password": "password",
        "host": "localhost",
        "port": 3306,
    },
    "node_args": {
        "host": "127.0.0.1",
        "port": 8888,
        "user": "rpcuser",
        "password": "rpcpass",
    },
    "show_dev_credit": True,
    "enforce_limit": True,
    "limit": 25,
    "enforce_invite": True,
    "invite": "your_invite_key",
    "should_send_mail": True,
    "mailgun_domain": "domain.com",
    "mailgun_key": "xxxxx",
    "scraper_sleep": 60
}


if os.path.exists(_CONFIG_FILE_PATH):
    with open(_CONFIG_FILE_PATH, mode='r') as handle:
        config = json.load(handle)

