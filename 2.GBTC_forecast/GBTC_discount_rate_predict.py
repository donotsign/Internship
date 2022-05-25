import csv
import pandas as pd
import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.arima.model import ARIMA

#在这里只需要将data.csv放入文件读取路径就能完成线性填充,参数length的意思是，想要用多少天的数据用于预测
def data_deal(length=200):
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
    #取出你想要用多长的数据用于预测（天）
    for_forcast=gbtc_data_filled['discount rate'][-length:]
    return for_forcast

def find_piq(length):
    data_forcast=pd.DataFrame(data_deal(length))
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


#i为想要往前预测几步
def forecast(length=200,i=1):
    data_forcast=data_deal(length)
    model = ARIMA(data_forcast, order=find_piq(length))#可以试着换成（1,1,1）
    result = model.fit()
    result.summary()
    result.conf_int()  # 系数显著
    forcast=result.forecast(i)
    return forcast


#最后输出结果是预测出来的一个series
example=forecast(300,2)