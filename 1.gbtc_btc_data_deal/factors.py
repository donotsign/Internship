import pandas as pd
import numpy as np


btc_data_close = pd.read_csv('btc_data_close.csv',index_col=0)

def vol(data=btc_data_close):
    factor1_vol=data['volume']
    return factor1_vol

def rsi(data=btc_data_close['close'], periods=10):
    length = len(data)
    rsies = [np.nan]*length
    #数据长度不超过周期，无法计算；
    if length <= periods:
        return rsies
    #用于快速计算；
    up_avg = 0
    down_avg = 0

    #首先计算第一个RSI，用前periods+1个数据，构成periods个价差序列;
    first_t = data[:periods+1]
    for i in range(1, len(first_t)):
        #价格上涨;
        if first_t[i] >= first_t[i-1]:
            up_avg += first_t[i] - first_t[i-1]
        #价格下跌;
        else:
            down_avg += first_t[i-1] - first_t[i]
    up_avg = up_avg / periods
    down_avg = down_avg / periods
    rs = up_avg / down_avg
    rsies[periods] = 100 - 100/(1+rs)

    #后面的将使用快速计算；
    for j in range(periods+1, length):
        up = 0
        down = 0
        if data[j] >= data[j-1]:
            up = data[j] - data[j-1]
            down = 0
        else:
            up = 0
            down = data[j-1] - data[j]
        #类似移动平均的计算公式;
        up_avg = (up_avg*(periods - 1) + up)/periods
        down_avg = (down_avg*(periods - 1) + down)/periods
        rs = up_avg/down_avg
        rsies[j] = 100 - 100/(1+rs)
    return rsies

def MA5(data=btc_data_close):
     ma5= data['close'].rolling(window=5).mean().dropna()
     return ma5

def MA10(data=btc_data_close):
    ma10 = data['close'].rolling(window=10).mean().dropna()
    return ma10

def bias6(data=btc_data_close):
    bias6 = (data['close'] - data['close'].rolling(6, min_periods=1).mean())/ data['close'].rolling(6, min_periods=1).mean()*100
    bias6 = round(data['bias_6'], 2)
    return bias6


factors=pd.DataFrame()
factors=factors.append(btc_data_close)
qq=pd.DataFrame(rsi())
qq.index=qq.set_index(factors.index)
factors=factors.append(qq)
