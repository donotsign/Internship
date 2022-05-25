"""
 Created on 2022/4/18
 @author  : ivy
 @File    : get_accrual.py
 @Description: 获取所有存续订单号
"""


import time
import json
import urllib.parse
import hmac
import hashlib
import pandas as pd
import requests
import base64

#用于获取gbtc和btc数据并计算新一天的折价率

def gen_timestamp():
    return int(time.time())


def gen_headers(time_stamp, key, sig):
    headers = {
        'Api-Timestamp': str(time_stamp),
        'Api-Key': key,
        'Api-Signature': sig,
        'Content-Type': 'application/json'
    }
    return headers


def gen_sign(secret, verb, path, timestamp, data=None):
    if data is None:
        data_str = ''
    else:
        assert isinstance(data, dict)
        # server并不要求 data_str按 key排序，只需此处 用来签名的 data_str和所发送请求中的data相同即可，是否排序请按实际情况选择
        data_str = json.dumps(data)
    message = verb + path + str(timestamp) + data_str
    print("message:", message)
    signature = hmac.new(base64.b64decode(secret), bytes(message, 'utf8'), digestmod=hashlib.sha256)
    signature = base64.b64encode(signature.digest()).decode()
    print('signature:', signature)

    return signature


def get_single_tick(verb='GET',mode='production',path='/otc-assets/broker/loan/records?type=accrual&is_deleted={}'):
    json_info = json.load(open("../ding.json"))
    if mode == 'production':
        cam_api_info = json_info['cam_api']
        url = json_info['cam_base_url']['business_url']
    elif mode == 'test':
        cam_api_info = json_info['test_cam_api']
        url = json_info['cam_base_url']['test_url']
    else:
        raise Exception('please input right mode!')
    print('==========url↓==========')
    print(url)
    print('==========api↓==========')
    print(cam_api_info)
    api_key = cam_api_info['api']
    api_secret = cam_api_info['secret']

    timestamp = gen_timestamp()
    sig = gen_sign(api_secret, verb, path, timestamp)
    headers = gen_headers(timestamp, api_key, sig)
    try:
        resp = requests.get(url + path, headers=headers)
    except Exception as e:
        print('error in get_single_tick() in data.py, error type is ',str(e))
    return resp.json()




def get_all_accrual(mode='test'):
    #mode='test'
    verb='GET'
    #share=0.00092856
    try:
        all_order = get_single_tick(verb='GET',mode=mode)
    except Exception as e:
        print('can not get new data')
        print(all_order)

    all_alias=[]
    for i in all_order['data']:
        all_alias.append(i['alias'])

    return all_alias

#获取实时价格
async def get_price_usdt(coin):
    path='/quote/batch-ticks?contracts=index/{}.usdt'.format(coin)
    try:
        price=get_single_tick(verb='GET',mode='test',path=path)
    except Exception as e:
        print('can not get new data')
    #print(price)
    return price['data'][0]['last']




