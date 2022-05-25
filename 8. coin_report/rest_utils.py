# -*- coding: utf-8 -*-
# @Time    : 6/28/2019 5:45 PM
# @Author  : Nicole
# @File    : rest_utils.py
# @Software: PyCharm
# @Description:


import time
import base64
import hmac
import hashlib
import json
import urllib
import datetime
import requests

# timeout in 5 seconds:
TIMEOUT = 5
ratelimit_remaining = 999
ratelimit_interval = 1000


# 各种请求,获取数据方式
def http_get_request(url, params, add_to_headers=None):
    global ratelimit_remaining
    global ratelimit_interval
    headers = {
        "Content-type": "application/x-www-form-urlencoded",
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = urllib.parse.urlencode(params)
    try:
        if ratelimit_remaining <= 0:
            time.sleep(ratelimit_interval / 1000)
        response = requests.get(url, postdata, headers=headers, timeout=TIMEOUT)
        if response.status_code == 200:
            ratelimit_remaining = float(response.headers.get('ratelimit-remaining', ratelimit_remaining))
            ratelimit_interval = float(response.headers.get('ratelimit-interval', ratelimit_interval))
            return response.json()
        else:
            return {"status": "fail"}
    except Exception as e:
        print("httpGet failed, detail is:%s" % e)
        return {"status": "fail", "msg": "%s" % e}


def http_post_request(url, params, add_to_headers=None):
    global ratelimit_remaining
    global ratelimit_interval
    headers = {
        "Accept": "application/json",
        'Content-Type': 'application/json',
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:53.0) Gecko/20100101 Firefox/53.0'
    }
    if add_to_headers:
        headers.update(add_to_headers)
    postdata = json.dumps(params)
    try:
        if ratelimit_remaining <= 0:
            time.sleep(ratelimit_interval / 1000)
        response = requests.post(url, postdata, headers=headers, timeout=TIMEOUT, verify=False)
        if response.status_code == 200:
            ratelimit_remaining = float(response.headers.get('ratelimit-remaining', ratelimit_remaining))
            ratelimit_interval = float(response.headers.get('ratelimit-interval', ratelimit_interval))
            return response.json()
        else:
            return response.json()
    except Exception as e:
        print("httpPost failed, detail is:%s" % e)
        return {"status": "fail", "msg": "%s" % e}


def api_key_get(url, request_path, params, ACCESS_KEY, SECRET_KEY):
    method = 'GET'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params.update({'AWSAccessKeyId': ACCESS_KEY,
                   'SignatureMethod': 'HmacSHA256',
                   'SignatureVersion': '2',
                   'Timestamp': timestamp})

    host_name = host_url = url
    # host_name = urlparse.urlparse(host_url).hostname
    host_name = urllib.parse.urlparse(host_url).netloc
    host_name = host_name.lower()

    params['Signature'] = createSign(params, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path
    return http_get_request(url, params)


def api_key_post(url, request_path, params, ACCESS_KEY, SECRET_KEY):
    method = 'POST'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params_to_sign = {'AWSAccessKeyId': ACCESS_KEY,
                      'SignatureMethod': 'HmacSHA256',
                      'SignatureVersion': '2',
                      'Timestamp': timestamp}

    host_url = url
    # host_name = urlparse.urlparse(host_url).hostname
    host_name = urllib.parse.urlparse(host_url).netloc
    host_name = host_name.lower()
    params_to_sign['Signature'] = createSign(params_to_sign, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
    return http_post_request(url, params)


def createSign(pParams, method, host_url, request_path, secret_key):
    sorted_params = sorted(pParams.items(), key=lambda d: d[0], reverse=False)
    encode_params = urllib.parse.urlencode(sorted_params)
    payload = [method, host_url, request_path, encode_params]
    payload = '\n'.join(payload)
    payload = payload.encode(encoding='UTF8')
    secret_key = secret_key.encode(encoding='UTF8')
    digest = hmac.new(secret_key, payload, digestmod=hashlib.sha256).digest()
    signature = base64.b64encode(digest)
    signature = signature.decode()
    return signature


def api_key_get_hb(url, request_path, params, ACCESS_KEY, SECRET_KEY):
    method = 'GET'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params.update({'AccessKeyId': ACCESS_KEY,
                   'SignatureMethod': 'HmacSHA256',
                   'SignatureVersion': '2',
                   'Timestamp': timestamp})

    host_name = host_url = url
    # host_name = urlparse.urlparse(host_url).hostname
    host_name = urllib.parse.urlparse(host_url).netloc
    host_name = host_name.lower()

    params['Signature'] = createSign(params, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path
    return http_get_request(url, params)


def api_key_post_hb(url, request_path, params, ACCESS_KEY, SECRET_KEY):
    method = 'POST'
    timestamp = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S')
    params_to_sign = {'AccessKeyId': ACCESS_KEY,
                      'SignatureMethod': 'HmacSHA256',
                      'SignatureVersion': '2',
                      'Timestamp': timestamp}
    host_url = url
    # host_name = urlparse.urlparse(host_url).hostname
    host_name = urllib.parse.urlparse(host_url).netloc
    host_name = host_name.lower()
    params_to_sign['Signature'] = createSign(params_to_sign, method, host_name, request_path, SECRET_KEY)
    url = host_url + request_path + '?' + urllib.parse.urlencode(params_to_sign)
    return http_post_request(url, params)


def http_get_request_hb(url, params):
    postdata = urllib.parse.urlencode(params)
    try:
        response = requests.get(url, postdata, timeout=TIMEOUT)
        if response.status_code == 200:
            return response.json()
        else:
            return {"status": "fail"}
    except Exception as e:
        print("httpGet failed, detail is:%s" % e)
        return {"status": "fail", "msg": "%s" % e}
