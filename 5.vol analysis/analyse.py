'''
Create on: 2020.2.24
@author: ivy
@file: analyse.py
@describe: 对各个币种进行流动性分级
'''

from websocket import create_connection
import gzip
import json
import pandas as pd
import time
from datetime import datetime
from get_ticker import *
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import string


avg_vol_90d=pd.read_csv('avg_vol_90d.csv',index_col=0)
#avg_vol_90d_df=pd.DataFrame.from_dict(avg_vol_90d,orient='index',columns=['avg_vol_90d'])
#avg_vol_90d_df.to_csv('avg_vol_90d.csv')
avg_vol_90d_df=avg_vol_90d.sort_values(by='avg_vol_90d',ascending=False)
plt.rcParams['font.sans-serif']=['SimSun']
sns.distplot(avg_vol_90d_df['avg_vol_90d'],kde=True,bins=50,rug=True)
plt.show()

k1=avg_vol_90d_df
k2=k1.drop(['btcusdt','ethusdt'])
plt.rcParams['font.sans-serif'] = ['SimSun']
sns.distplot(k2['avg_vol_90d'], kde=True, bins=50, rug=True)
plt.show()

k2['avg_vol_90d'].quantile(0.9)
k2['avg_vol_90d'].quantile(0.7)
k2['avg_vol_90d'].quantile(0.4)

q1=[]
q2 =[]
q3 =[]
q4 =[]


qq=k2['avg_vol_90d']
for i in k2['avg_vol_90d']:
    if i>k2['avg_vol_90d'].quantile(0.75):
        q1.append(i)
    elif i>k2['avg_vol_90d'].quantile(0.5):
        q2.append(i)
    elif i>k2['avg_vol_90d'].quantile(0.25):
        q3.append(i)
    else:
        q4.append(i)


k2['avg_vol_90d'].values

total_vol=np.sum(avg_vol_90d_df['avg_vol_90d'])
np.sum(q4)/total_vol


v1=[]
v2 =[]
v3 =[]
v4 =[]



for i in k2['avg_vol_90d']:
    if i>50000000:
        v1.append(i)
    elif i>10000000:
        v2.append(i)
    elif i>5000000:
        v3.append(i)
    else:
        v4.append(i)

np.sum(v4)/total_vol

high_vol=avg_vol_90d_df['lunausdt':'nexousdt']
plt.rcParams['font.sans-serif'] = ['SimSun']
sns.distplot(high_vol['avg_vol_90d'], kde=True, bins=50, rug=True)
plt.show()

q1h =[]
q2h =[]
q3h =[]
q4h =[]


qq=k2['avg_vol_90d']
for i in high_vol['avg_vol_90d']:
    if i>high_vol['avg_vol_90d'].quantile(0.75):
        q1h.append(i)
    elif i>high_vol['avg_vol_90d'].quantile(0.5):
        q2h.append(i)
    elif i>high_vol['avg_vol_90d'].quantile(0.25):
        q3h.append(i)
    else:
        q4h.append(i)

high_vol['avg_vol_90d'].quantile(0.25)
total_vol=np.sum(high_vol['avg_vol_90d'])
np.sum(q4h)/total_vol

v1h =[]
v2h =[]
v3h =[]
v4h =[]
v5h =[]
v6h =[]

for i in k2['avg_vol_90d']:
    if i>75000000:
        v1h.append(i)
    elif i>60000000:
        v2h.append(i)
    elif i>45000000:
        v3h.append(i)
    elif i>30000000:
        v4h.append(i)
    elif i>15000000:
        v5h.append(i)
    else:
        v6h.append(i)

np.sum(v1h)/total_vol

print(high_vol.index)
qq=list(high_vol.index)

for i in range(len(qq)):
    qq[i]=qq[i][:-4]

for i in range(len(qq)):
    qq[i]=qq[i].upper()


zhanye=['filusdt','ltcusdt','bchusdt','bsvusdt','trxusdt','linkusdt','paxusdt','etcusdt',
                      'bnbusdt','adausdt','dogeusdt','xlmusdt','xmrusdt','eosusdt','compusdt','dashusdt',
                       'zecusdt','solusdt','avaxusdt','axsusdt','shibusdt',
                       'sandusdt','sklusdt','dydxusdt','btcusdt','ethusdt','iotausdt',
                       '1inchusdt','sushiusdt','dotusdt','uniusdt','wbtcusdt','aaveusdt','crousdt']

cc=dict()
for i in zhanye:
    cc[i]=avg_vol_90d_df['avg_vol_90d'][i]

cc=pd.DataFrame([cc])
cc=cc.T
cc.columns=['avg_vol_90d']
cc_df=cc.sort_values(by='avg_vol_90d',ascending=False)
sns.distplot(cc['avg_vol_90d'],kde=True,bins=50,rug=True)
plt.show()

c=cc_df.drop(['btcusdt','ethusdt'])
plt.rcParams['font.sans-serif'] = ['SimSun']
sns.distplot(c['avg_vol_90d'], kde=True, bins=50, rug=True)
plt.show()

c['avg_vol_90d'].quantile(1/3)
c['avg_vol_90d'].quantile(2/3)


q1=[]
q2 =[]
q3 =[]


qq=c['avg_vol_90d']
for i in c['avg_vol_90d']:
    if i>c['avg_vol_90d'].quantile(2/3):
        q1.append(i)
    elif i>c['avg_vol_90d'].quantile(1/3):
        q2.append(i)
    else:
        q3.append(i)


c['avg_vol_90d'].values

total_vol=np.sum(cc['avg_vol_90d'])
np.sum(q3)/total_vol

cd=list(c.index)

for i in range(len(cd)):
    cd[i]=cd[i][:-4]

for i in range(len(cd)):
    cd[i]=cd[i].upper()