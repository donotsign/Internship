'''
Create on: 2020.2.24
@author: ivy
@file: get_ticker.py
@describe: 获取交易所所有交易对
'''

import requests
def get_ticker():
    url = "https://api.huobi.pro/market/tickers"
    test = requests.get(url)
    test = test.json()
    print(test)
    all_ticker=[]
    ticker=test
    for i in ticker['data']:
        all_ticker.append(i['symbol'])
    target_ticker=[]
    for j in all_ticker:
        if j[-4:] == 'usdt' and j[-6:-4] not in ['3l','3s','2l','2s','1l','1s']:
            target_ticker.append(j)
    return target_ticker

#ticker=get_ticker()