'''
Create on: 2020.2.17
@author: ivy
@file: data.py
@describe: 预测gbtc折价率
'''

import csv
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA
import datetime
from data import *


#在这里只需要将data.csv放入文件读取路径就能完成线性填充,参数length的意思是，想要用多少天的数据用于预测
def data_deal():#这个只要第一次运行就行，后面不用了
    data = pd.read_csv('data.csv', index_col=0)
    start_date=data[-1:].index.tolist()[0]
    end_date=data[0:1].index.tolist()[0]

    gbtc_data = data.loc[:start_date, ["Holdings/Share", "Market Price/Share"]]

    # 线性填充GBTC数据
    date_index = pd.date_range(start_date, end_date)
    gbtc_data.index = pd.to_datetime(gbtc_data.index)

    gbtc_data_filled = gbtc_data.reindex(date_index)
    gbtc_data_filled = gbtc_data_filled.interpolate(method='linear')

    gbtc_data_filled.to_csv("gbtc_data_filled.csv")

    # 读取数据
    gbtc_data_filled = pd.read_csv('gbtc_data_filled.csv', index_col=0)

    # 算出溢价率
    gbtc_data_filled['discount rate'] = (gbtc_data_filled['Market Price/Share'] - gbtc_data_filled['Holdings/Share']) / \
                                        gbtc_data_filled['Holdings/Share']

    discount_rate=pd.DataFrame(gbtc_data_filled['discount rate'])
    discount_rate.to_csv("discount_rate.csv")

def read_data_renew(length=300): #取出你想要用多长的数据用于预测（天）顺便更新数据！！！！
    data = pd.read_csv('discount_rate.csv', index_col=0)
    saved_last=pd.read_csv('save_last.csv',index_col=0)
    saved_last=float(saved_last["last"])

    new_last = get_single_tick(verb='GET', kind='gbtc')
    new_last = new_last['data'][0]
    new_last = float(new_last['last'])

    saved_predict=pd.read_csv('save_predict.csv')
    saved_predict=float(saved_predict['0'])

    start_date = data[-1:].index.tolist()[0]
    end_date = data[0:1].index.tolist()[0]
    today=datetime.date.today()
    today=str(today)
    if today !=start_date:
        if saved_last==new_last:
            try:
                add = dict({'discount rate': saved_predict})
                add = pd.DataFrame([add])
                add.index = [today]
                data = data.append(add)
                for_forecast = data[-length:]
            except Exception as e:
                print('error in renew_data,when in close day,error type is',str(e))

        else:
            try:
                new=get_new_data()
                add=dict({'discount rate':new})
                add=pd.DataFrame([add])
                add.index=[today]
                data=data.append(add)
                for_forecast=data[-length:]
            except Exception as e:
                print('error in renew_data, when in open day,error type is ',str(e))
         #  except Exception as e:
           #    print('error in renew data(open day),error type is ', str(e))
    else:
        for_forecast=data[-length:]

    check_blank = data.loc[:today]

    #检查是否有空日期，不然在预测的时候会报错，顺便将日期格式进行统一。
    check_blank_index = pd.date_range(end_date,today)
    check_blank.index = pd.to_datetime(check_blank.index)

    check_blank = check_blank.reindex(check_blank_index)
    check_blank = check_blank.interpolate(method='linear')
    check_blank.to_csv("discount_rate.csv")

    return for_forecast


def find_piq(length):
    data_forcast=pd.DataFrame(read_data_renew(length))
    i = 0
    while True:
        data_forcast_di = data_forcast.diff(i).dropna()
        result = sm.tsa.stattools.adfuller(data_forcast_di)
        if result[1] <= 0.01:
            break
        else:
            i = i + 1


    P=[0,1,2,3,4,5]
    Q=[0,1,2,3,4,5]
    BIC=10000000000
    f_p=0
    f_q=0
    for p in P:
        for q in Q:
            model = ARIMA(data_forcast,order=(p,i,q))
            result=model.fit()
            if result.bic <BIC:
                BIC=result.bic
                f_p=p
                f_q=q

    return(f_p,i,f_q)

#length为i为想要往前预测几步
def forecast(length=200,i=1):

    #length=300
    #i=1
    #data_forcast= pd.read_csv('discount_rate.csv', index_col=0)
    data_forcast=read_data_renew(length)
    try:
        model = ARIMA(data_forcast, order=find_piq(length))#可以试着换成（1,1,1）
    except Exception as e:
        print('error in forcast, error type is ',str(e))
    result = model.fit()
    result.summary()
    result.conf_int()  # 系数显著
    forcast = result.forecast(i)
    save_predict=pd.DataFrame(forcast)
    save_predict.to_csv('save_predict.csv')

    return forcast


#最后输出结果是预测出来的一个series
#example=forecast(300,1)