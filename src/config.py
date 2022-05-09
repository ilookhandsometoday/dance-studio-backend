import yaml
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()
if bool(os.getenv('BACKEND_DEBUG')):
    logger.setLevel(logging.DEBUG)

def get_config():
    with open('config.yml') as config_file:

        config = yaml.safe_load(config_file)
        app = config['app']
        postgres_conn = config['postgres']['conn_string']
        host = app['host']
        port = app['port']
        return host, port, postgres_conn
