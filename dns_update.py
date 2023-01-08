import requests
import json
import logging
import yaml
from time import sleep


def get_ip():
    while True:
        try:
            ip = requests.get('http://ip.42.pl/raw').text
            logger.debug(f'current_ip: {current_ip}')
            return ip
        except Exception:
            logger.exception('ip scrape error')
            sleep(30)

def get_object_id(request_url, request_headers, name):

    result = requests.get(request_url, headers = request_headers).text
    result = json.loads(result)

    object_id = [ item['id'] for item in result['result'] if item['name'] == name ]

    return object_id[0]

def update_dns(request_url, request_headers, new_ip):
    
    request_params = {'content': new_ip}

    while True:
        try:
            result = requests.patch(request_url, json = request_params, headers = request_headers).text
            result = json.loads(result)
            logger.info(result)
            if result['success']:
                logger.info('updated')
                return 
        except Exception:
            logger.exception('error updating cloudflare logs')

        sleep(20)

# read config

with open ('./dns_update.yaml', 'r', encoding = 'utf-8') as file:
    config = yaml.safe_load(file) 

log_level = config['log']['level']
log_path= config['log']['path']
token = config['api_token']
zone_name = config['zone_name']
domain_name = config['domain_name']
dns_url = config['base_url']

# create logger
logging.basicConfig(filename=log_path, format='%(asctime)s %(message)s',filemode='a')
logger = logging.getLogger()
if log_level.lower() == 'debug':
    logger.setLevel(logging.DEBUG)
elif log_level.lower() == 'info':
    logger.setLevel(logging.INFO)
else:
    raise ValueError('Invalid Log Level')


# run main code
logger.info('starting')

dns_headers = {'Authorization': f'Bearer {token}'}

zone = get_object_id(dns_url, dns_headers, zone_name)

dns_url += f'{zone}/dns_records/' 
record = get_object_id(dns_url, dns_headers, domain_name)

dns_url += f'{record}' 

current_ip = None

while True:
    ip = get_ip()

    if current_ip != ip:
        update_dns(dns_url, dns_headers, ip)
        current_ip = ip
    else:
        logger.debug('no need to update')

    sleep(30)

