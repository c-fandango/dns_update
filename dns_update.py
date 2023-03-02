'''script to change cloudflare dns record upon change to public ip of rpi'''
import json
import yaml
import logging
import requests
import argparse
from time import sleep

def load_config(path):

    with open (path, 'r', encoding = 'utf-8') as file:
        config = yaml.safe_load(file)

    return config

def get_ip():
    '''queries url to obtain current public ip address'''
    try:
        ip_address = requests.get('http://icanhazip.com').text
        logger.debug('ip: {%s}', ip_address)
        return ip_address
    except Exception:
        logger.exception('ip scrape error')

    return ''

def get_object_id(request_url, request_headers, name):
    '''gets cloudflare zone id from zone name'''
    result = requests.get(request_url, headers = request_headers).text
    result = json.loads(result)

    object_id = [ item['id'] for item in result['result'] if item['name'] == name ]

    return object_id[0]

def update_dns(request_url, request_headers, new_ip):
    '''send request to cloudflare with api to update record with new IP'''

    request_params = {'content': new_ip}

    try:
        result = requests.patch(request_url, json = request_params, headers = request_headers).text
        result = json.loads(result)
        if result['success']:
            logger.info('updated')
            return True
        else:
            logger.error('query unsucessful')
    except Exception:
        logger.exception('error updating cloudflare logs')
    return False

def run( zone_name, domain_name, api_url, token):
    '''main code control loop'''
    dns_headers = {'Authorization': f'Bearer {token}'}

    zone = get_object_id(api_url, dns_headers, zone_name)

    api_url += f'{zone}/dns_records/'
    api_url += get_object_id(api_url, dns_headers, domain_name)

    stored_ip = None

    while True:
        current_ip = get_ip()

        if current_ip != stored_ip and update_dns(api_url, dns_headers, current_ip):
            stored_ip = current_ip
            assert current_ip, 'current_ip is None, something has gone wrong'
        else:
            logger.info('not updating record')
            sleep(30)

# parse args 
parser = argparse.ArgumentParser(description = 'service for updating dns records when public ip changes')
parser.add_argument('config_path')
args = parser.parse_args()

config = load_config(args.config_path)

log_level = config['log']['level']

# create logger
logging.basicConfig(filename=config['log']['path'], format='%(asctime)s %(message)s', filemode='a')
logger = logging.getLogger()
if log_level.lower() == 'debug':
    logger.setLevel(logging.DEBUG)
elif log_level.lower() == 'info':
    logger.setLevel(logging.INFO)
else:
    raise ValueError('Invalid Log Level')

# run main code
if __name__ == '__main__':
    logger.info('starting')
    run( config['zone_name'], config['domain_name'], config['api_url'], config['api_token'] )
