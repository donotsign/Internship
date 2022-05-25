"""
 Created on 2022/2/8
 @author  : ivy
 @File    : data_deal.py
 @Description: 处理原始数据
"""
import pandas as pd

def data_deal():
    data=pd.read_csv('data.csv' , index_col=0)
    btc_data=pd.read_csv('btc_data.csv',index_col=0)


    #为了区分冬时令和夏时令，冬时令5：00休市，夏时令4:00休市，美国时间比我们晚，所以
    btc_data1=btc_data[:"2020/3/2 23:59"]
    btc_data1=btc_data1[[i%1440==0 for i in range(len(btc_data1.index))]]

    btc_data2=btc_data["2020/3/3 4:00":"2020/10/31 23:59"]
    btc_data2=btc_data2[[i%1440==0 for i in range(len(btc_data2.index))]]

    btc_data3=btc_data["2021/3/14 5:00":"2021/3/14 23:59"]
    btc_data3=btc_data3[[i%1440==0 for i in range(len(btc_data3.index))]]

    btc_data4=btc_data["2021/3/15 4:00":"2021/11/6 5:00"]
    btc_data4=btc_data4[[i%1440==0 for i in range(len(btc_data4.index))]]

    btc_data5=btc_data["2021/11/7 5:00":]
    btc_data5=btc_data5[[i%1440==0 for i in range(len(btc_data5.index))]]
    #最终得到和gbtc close价格时间相对应的数据
    btc_data_close=pd.concat([btc_data1,btc_data2,btc_data3,btc_data4,btc_data5])

    gbtc_data=data.loc[:"2019/12/31",["Holdings/Share","Market Price/Share"]]

    #线性填充GBTC数据
    date_index=pd.date_range('2019/12/31','2022/2/8')
    gbtc_data.index = pd.to_datetime(gbtc_data.index)

    gbtc_data_filled=gbtc_data.reindex(date_index)
    gbtc_data_filled=gbtc_data_filled.interpolate(method='linear')

    gbtc_data_filled.to_csv("gbtc_data_filled.csv")
    btc_data_close.to_csv("btc_data_close.csv")

    vix=pd.read_csv('vix.csv' , index_col=0)

    vix=vix.iloc[::-1]
    date_index=pd.date_range('2020/01/01','2022/2/8')
    vix.index = pd.to_datetime(vix.index)
    vix=vix.reindex(date_index)
    vix=vix.interpolate(method='linear')

    bp500=pd.read_csv('bp500.csv',index_col=0)

    bp500=bp500.iloc[::-1]
    date_index=pd.date_range('2020/01/01','2022/02/08')
    bp500.index = pd.to_datetime(bp500.index)
    bp500=bp500.reindex(date_index)
    bp500=bp500.interpolate(method='linear')

    vix.to_csv("vix_filled.csv")
    bp500.to_csv("bp500—filled.csv")