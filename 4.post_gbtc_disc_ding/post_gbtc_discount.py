'''
Create on: 2020.2.22
@author: ivy
@file: post_gbtc_discount.py
@describe: 设置gbtc折价率并用钉钉机器人实时监控
'''
import asyncio
import datetime
import time
import json
import urllib.parse
import hmac
import hashlib
import requests
import base64
from predict import *
import calendar
import aiohttp


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


async def get_single_tick(verb='GET', p_data=None):
    mode = 'test'
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

    if verb == 'GET':
        '''获取价格'''
        #path = '/quote/batch-ticks?contracts=index/gbtc.usd'
        '''获取价格'''
        '''↓↓↓获取 GBTC 折价率'''
        path = '/otc-assets/broker/loan/collateral-valuation-haircut-setting'


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
        # path += ",".join([''])
        '''↑↑↑订单信息实时查询'''

        timestamp = gen_timestamp()
        sig = gen_sign(api_secret, verb, path, timestamp)
        headers = gen_headers(timestamp, api_key, sig)
        try:
            resp = requests.get(url + path, headers=headers)
        except Exception as e:
            await print('error in GET, error type is ',str(e))
        return resp.json()


    elif verb == 'POST':
        '''↓↓↓设置 GBTC 折价率'''
        path = '/otc-assets/broker/loan/collateral-valuation-haircut-setting'
        '''↑↑↑设置 GBTC 折价率'''

        post_data = p_data

        timestamp = gen_timestamp()
        sig = gen_sign(api_secret, verb, path, timestamp, post_data)
        headers = gen_headers(timestamp, api_key, sig)
        try:
            resp = requests.post(url + path, headers=headers, data=json.dumps(post_data).encode('utf-8'))
        except Exception as e:
            await print('error in POST, error type is ',str(e))
        return resp.json()


async def post_gbtc_discount_rate():
    today=datetime.date.today()
    weekday=calendar.weekday(today.year,today.month,today.day)

    forcast_discount_rate= forecast(300,1)
    forcast_discount_rate=str(forcast_discount_rate[0]*(-1))

    #判断是不是周末，非周末post休市时间，周末post一整天
    if weekday<=4:
       post_data = {
            "data": [
                {
                   "underlying": "gbtc",
                   "week_section": [1, 1, 1, 1, 1, 0, 0],
                   "start_time": "16:00",
                   "end_time": "9:30",
                   "timezone": "+08:00",
                   "discount_rate": forcast_discount_rate,
                }
            ]
        }
    else:
        post_data = {
            "data": [
                {
                    "underlying": "gbtc",
                    "week_section": [0, 0, 0, 0, 0, 1, 1],
                    "start_time": "00:00",
                    "end_time": "24:00",
                    "timezone": "+08:00",
                    "discount_rate": forcast_discount_rate,
                }
            ]
        }
    try:
        test = await get_single_tick(
            verb='POST',
            p_data=post_data
        )
    except Exception as e:
        await print('error in post_gbtc_discount_rate, error type is ', str(e))


    print(test)

    after_set = await get_single_tick(verb='GET')
    afterset=after_set['data'][0]['discount_rate']
    #afterset='0.06' 尝试报错
    curr_time=datetime.datetime.now()
    time=datetime.datetime.strftime(curr_time,'%Y-%m-%d %H:%M:%S')
    if afterset==forcast_discount_rate:
        send("现在时间是{}:\n预测的gbtc折价率为{}\n成功设置gbtc折价率为{}".format(time,forcast_discount_rate,afterset),0)
    else:
        send("现在时间是{}:\n出现设置值与系统上不一致!！\n预测的gbtc折价率为{}\n成功设置gbtc折价率为{}".format(time, forcast_discount_rate, afterset), 1)
    await asyncio.sleep(60)
    asyncio.ensure_future(post_gbtc_discount_rate())
    # for i in test:
    #     for j in test[i][0]:
    #         print("{}: {}".format(j, test[i][0][j]))
    #     print("====================")






def send(text,error=0):
    webhook = '****'
    timestamp=str(round(time.time()*1000))
    secret='****'
    secret_enc=secret.encode('utf-8')
    string_to_sign='{}\n{}'.format(timestamp,secret)
    string_to_sign_enc = string_to_sign.encode('utf-8')
    hmac_code = hmac.new(secret_enc,string_to_sign_enc,digestmod=hashlib.sha256).digest()
    sign=urllib.parse.quote_plus(base64.b64encode(hmac_code))
    if error==0:
        data = {
            'msgtype': 'text',
            'text': {
                'content': text
            }
        }
    else:
        data = {
            'msgtype': 'text',
            'text': {
                'content': text
            },
            'at':{
                "atMobiles":["*******"],"isAtAll":"false"
            }

        }


    headers = {'content-type': 'application/json;charset=utf-8'}
    requests.post('{}&timestamp={}&sign={}'.format(webhook, timestamp, sign), data=json.dumps(data),headers=headers)








if __name__ == "__main__":

    print('当前时间戳是',time.time())
    asyncio.ensure_future(post_gbtc_discount_rate())
    asyncio.get_event_loop().run_forever()




"""
更新过CAM 系统版本后就可以正常获取账户信息了. 如果以后出现了不能正常获取信息的情况, 那就有可能是版本的问题导致的, 这个时候就可以去问问
1token 的人是不是这么回事
"""

