'''
Create on: 2020.2.17
@author: ivy
@file: data.py
@describe: 获取历史gbtc折价率数据
'''

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


def get_single_tick(verb='GET', kind='gbtc'):
    mode = 'test'  #视情况修改
    json_info = json.load(open("ding.json"))
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
    # verb = 'GET'  # 可选项: GET & POST
    # path = '/quote/batch-ticks?contracts=index/eth.usdt,huobip/btc.usdt'
    # path = '/otc-assets/broker/loan/summary-lit'

    if kind == 'gbtc':
        '''获取价格'''
        path = '/quote/batch-ticks?contracts=index/gbtc.usd'
        '''获取价格'''
        '''↓↓↓获取 GBTC 折价率'''
        #path = '/otc-assets/broker/loan/collateral-valuation-haircut-setting'
        '''↑↑↑获取 GBTC 折价率'''

        '''↓↓↓借贷订单报警查询'''
        # start_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()) - 1 * 86400))
        # end_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()) + 7 * 86400))
        # start_time = start_time.split(" ")
        # start_time = "{}T{}.000Z".format(start_time[0], start_time[1])
        # end_time = end_time.split(" ")
        # end_time = "{}T{}.000Z".format(end_time[0], end_time[1])
        # status = 'trigger'
        #
        # path = "/riskcontrol/history/otc-loan/ltv/list?"
        # path += "begin={}&end={}&status={}".format(start_time, end_time, status)
        '''↑↑↑借贷订单报警查询'''

        '''↓↓↓订单信息实时查询'''
        # path = "/otc-assets/broker/loan/batch-records?type=loan_id&val="
        # path += ",".join(['211119845', '211119844', '211123477'])
        '''↑↑↑订单信息实时查询'''

        timestamp = gen_timestamp()
        sig = gen_sign(api_secret, verb, path, timestamp)
        headers = gen_headers(timestamp, api_key, sig)
        try:
            resp = requests.get(url + path, headers=headers)
        except Exception as e:
            print('error in get_single_tick() in data.py, error type is ',str(e))
        return resp.json()


    elif kind == 'btc':
        '''↓↓↓设置 GBTC 折价率'''
        path = '/quote/batch-ticks?contracts=index/btc.usd'
        '''↑↑↑设置 GBTC 折价率'''

        timestamp = gen_timestamp()
        sig = gen_sign(api_secret, verb, path, timestamp)
        headers = gen_headers(timestamp, api_key, sig)
        resp = requests.get(url + path, headers=headers)
        return resp.json()



def get_new_data():
    verb='GET'
    share=0.00092856
    try:
        new_gbtc = get_single_tick(verb='GET', kind='gbtc')
        new_btc = get_single_tick(verb='GET', kind='btc')
    except Exception as e:
        print('can not get new data')

    new_gbtc=new_gbtc['data'][0]
    save_last =pd.DataFrame([new_gbtc])
    save_last.to_csv('save_last.csv')
    new_gbtc=float(new_gbtc['last'])
    new_btc = new_btc['data'][0]
    new_btc=float(new_btc['last'])
    discount_rate=(new_gbtc-new_btc*share)/(new_btc*share)
    return discount_rate

get_single_tick()




