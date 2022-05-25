"""
 Created on 2022/5/6
 @author  : ivy
 @File    : get_price_4exchange.py
 @Description: 获取四个交易所现货平均价格
"""
import requests
import pandas as pd
import numpy as np


def huobi_price(symbol):
    try:
        contract_url = 'https://api-aws.huobi.pro/market/trade?symbol={}usdt'.format(symbol)
        response = requests.get(contract_url)
        #print(response.json())
        response.close()
        return response.json()['tick']['data'][0]['price']
    except:
        return 0



def binance_price(symbol):
    try:
        contract_url = 'https://fapi.binance.com/fapi/v1/ticker/price?symbol={}USDT'.format(symbol)
        response = requests.get(contract_url)
        #print(response.json())
        response.close()
        return response.json()['price']
    except:
        return 0

def okex_price(symbol):
    try:
        contract_url = 'https://aws.okx.com/api/v5/market/ticker?instId={}-USDT'.format(symbol)
        response = requests.get(contract_url)
        #print(response.json())
        response.close()
        return response.json()['data'][0]['last']
    except:
        return 0

def ftx_price(symbol):
    try:
        contract_url = 'https://ftx.com/api/markets/{}/USDT'.format(symbol)
        response = requests.get(contract_url)
        #print(response.json())
        response.close()
        return response.json()['result']['last']
    except:
        return 0


def get_avg_price(symbol):
    huobi_last_price = huobi_price(symbol.lower())
    binance_last_price= float(binance_price(symbol))
    okex_last_price = float(okex_price(symbol))
    ftx_last_price = ftx_price(symbol)
    prices=[huobi_last_price,binance_last_price,okex_last_price,ftx_last_price]
    total_price=0
    count=0
    for i in prices:
        if i !=0:
            total_price +=i
            count += 1

    average_last_price=total_price/count
    return average_last_price

#qq=get_avg_price('FIL')



