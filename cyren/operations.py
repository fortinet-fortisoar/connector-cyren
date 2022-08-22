""" Copyright start
  Copyright (C) 2008 - 2022 Fortinet Inc.
  All rights reserved.
  FORTINET CONFIDENTIAL & FORTINET PROPRIETARY SOURCE CODE
  Copyright end """


import json
import requests
from connectors.core.connector import get_logger, ConnectorError

logger = get_logger('cyren')


class Cyren(object):
    def __init__(self, config):
        bundle_type = config.get('select_bundle_type')
        if bundle_type == 'Free':
            self.base_url = config.get('server').strip() + '/api/v1/free'
        elif bundle_type == 'Security':
            self.base_url = config.get('server').strip() + '/api/v1/security'
        elif bundle_type == 'Complete':
            self.base_url = config.get('server').strip() + '/api/v1/complete'
        jwt = config.get('token')
        self.headers = {'Authorization': 'Bearer ' + jwt, 'Content-Type': 'application/json'}
        if not self.base_url.startswith('https://'):
            self.base_url = 'https://' + self.base_url

    def make_rest_call(self, method='POST', data=None, endpoint=None, health_check=False):
        url = self.base_url + endpoint
        logger.debug('Final url to make rest call is: {0}'.format(url))
        if data:
            logger.debug('Converting the data: {0} into an equivalent JSON object.'.format(data))
            data = json.dumps(data)
            logger.debug('After converting into a JSON object: {0}'.format(data))
        try:
            logger.debug(
                'Making a request with {0} method, {1} data and {2} as headers.'.format(method, data, self.headers))
            response = requests.request(method, url, data=data, headers=self.headers)
            if response.status_code in [200]:
                if health_check:
                    return {'status': 'Success'}
                try:
                    logger.debug('Converting the response into JSON format after returning with status code: {0}'.format(
                        response.status_code))
                    response_data = response.json()
                    return {'status': response_data['status'] if 'status' in response_data else 'Success',
                            'data': response_data}
                except Exception as e:
                    response_data = response.content
                    logger.error('Failed with an error: {0}. The response details are: {1}'.format(e, response_data))
                    return {'status': 'Failure', 'data': response_data}
            else:
                logger.error('Failed with response {0}'.format(response))
                raise ConnectorError(
                    {'status': 'Failure', 'status_code': str(response.status_code), 'response': response})
        except Exception as e:
            logger.exception(str(e))
            raise ConnectorError(str(e))

    def handle_params(self, params):
        input_type = params.get('input_type')
        value = params.get('value')
        logger.debug("The given input type is: {0} and value is: {1}".format(input_type, value))
        if input_type == 'Single URL' and isinstance(value, str):
            endpoint = '/url'
            data = {'url': value}
        elif input_type == 'Batch of URLs' and isinstance(value, list):
            endpoint = '/urls-list'
            data = {'urls': value}
        else:
            logger.error("Either input type or the given value is incorrect.")
            raise ConnectorError("Either input type or the given value is incorrect.")
        input_details = {'endpoint': endpoint, 'data': data}
        return input_details

    def get_url_lookup(self, params):
        logger.info('Getting input parameters')
        inputs = self.handle_params(params)
        logger.debug('Endpoint is: {0}'.format(inputs['endpoint']))
        logger.debug('Payload data is: {0}'.format(inputs['data']))
        return self.make_rest_call(endpoint=inputs['endpoint'], data=inputs['data'])


def _run_operation(config, params):
    cc_obj = Cyren(config)
    command = getattr(Cyren, params['operation'])
    response = command(cc_obj, params)
    return response


def _check_health(config):
    try:
        cc_obj = Cyren(config)
        data = {"url": "cyren.com"}
        server_config = cc_obj.make_rest_call(endpoint='/url', data=data, health_check=True)
        if server_config['status'] == 'Failure':
            logger.exception('Authentication Error, Check URL and API Token.')
            raise ConnectorError('Authentication Error, Check URL and API Token.')
        return True
    except Exception as Err:
        logger.exception('Health check failed with: {0}'.format(Err))
        raise ConnectorError('Health check failed with: {0}'.format(Err))
