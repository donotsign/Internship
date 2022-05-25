"""
 Created on 2022/2/10
 @author  : ivy
 @File    : arima.py
 @Description: 尝试使用arima模型预测gbtc折价率
"""

import csv
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import scipy as stats
import statsmodels.api as sm
from scipy import stats
from statsmodels.tsa.stattools import adfuller
from statsmodels.tsa.arima.model import ARIMA



def data_deal():
    data = pd.read_csv('data.csv', index_col=0)
    '''
    btc_data = pd.read_csv('btc_data.csv', index_col=0)

    # 为了区分冬时令和夏时令，冬时令5：00休市，夏时令4:00休市，美国时间比我们晚，所以
    btc_data1 = btc_data[:"2020/3/2 23:59"]
    btc_data1 = btc_data1[[i % 1440 == 0 for i in range(len(btc_data1.index))]]

    btc_data2 = btc_data["2020/3/3 4:00":"2020/10/31 23:59"]
    btc_data2 = btc_data2[[i % 1440 == 0 for i in range(len(btc_data2.index))]]

    btc_data3 = btc_data["2021/3/14 5:00":"2021/3/14 23:59"]
    btc_data3 = btc_data3[[i % 1440 == 0 for i in range(len(btc_data3.index))]]

    btc_data4 = btc_data["2021/3/15 4:00":"2021/11/6 5:00"]
    btc_data4 = btc_data4[[i % 1440 == 0 for i in range(len(btc_data4.index))]]

    btc_data5 = btc_data["2021/11/7 5:00":]
    btc_data5 = btc_data5[[i % 1440 == 0 for i in range(len(btc_data5.index))]]
    # 最终得到和gbtc close价格时间相对应的数据
    btc_data_close = pd.concat([btc_data1, btc_data2, btc_data3, btc_data4, btc_data5])
'''
    gbtc_data = data.loc[:"2019/12/31", ["Holdings/Share", "Market Price/Share"]]

    # 线性填充GBTC数据
    date_index = pd.date_range('2019/12/31', '2022/2/8')
    gbtc_data.index = pd.to_datetime(gbtc_data.index)

    gbtc_data_filled = gbtc_data.reindex(date_index)
    gbtc_data_filled = gbtc_data_filled.interpolate(method='linear')

    gbtc_data_filled.to_csv("gbtc_data_filled.csv")
    #btc_data_close.to_csv("btc_data_close.csv")

data_deal()

#------------------------------------------------------------------------------------------------------------------------
#这些是全局变量
#读取数据
gbtc_data_filled = pd.read_csv('gbtc_data_filled.csv' , index_col=0)

#算出溢价率
gbtc_data_filled['discount rate']=(gbtc_data_filled['Market Price/Share']-gbtc_data_filled['Holdings/Share'])/gbtc_data_filled['Holdings/Share']

# 区分训练集和测试集7：3
train_end = int(len(gbtc_data_filled) / 10 * 7)
train = gbtc_data_filled['discount rate'][:train_end]
test = gbtc_data_filled['discount rate'][train_end:]
test=pd.DataFrame(test)

#本部分用于检测数据，查看是否适合使用arima模型，事实证明使用，因此检验通过后在真实的预测中不运行
#'''---------------------------------------------------------------------------------------------------------------

plt.rcParams['axes.unicode_minus'] = False  # 用来正常显示负号
train.plot()
plt.title("Discount Rate")  # 添加图标题
plt.xticks(rotation=45)  # 横坐标旋转45度
plt.xlabel('date')  # 添加图的标签（x轴，y轴）
plt.ylabel('price/usd')

from statsmodels.graphics.tsaplots import plot_acf  # 导入自相关函数

plot_acf(train, use_vlines=True, lags=30)  # "lags"自相关函数的滞后取值范围，此处之后30阶，绘制出原始数据自相关图
plt.show()

result = sm.tsa.stattools.adfuller(train)
print(result)
# 无法拒绝原假设，时间序列非平稳

# 进行差分再次检验
train_d1 = train.diff(1).dropna()
train_d1.columns = [u'train_diff1']
train_d1.plot()  # 绘制出差分后的时序图
plt.title("Renshou Insurance Open")  # 添加图标题
plt.show()  # 展示差分后的时序图
result = sm.tsa.stattools.adfuller(train_d1)
print(result)
# 拒绝原假设，一阶差分之后，时间序列平稳

# 绘制差分后自相关图与偏自相关图
from statsmodels.graphics.tsaplots import plot_acf  # 导入自相关函数
plot_acf(train_d1, use_vlines=True, lags=30)
plt.show()

from statsmodels.graphics.tsaplots import plot_pacf  # 导入偏自相关函数
plot_pacf(train_d1, use_vlines=True, lags=30)
plt.show()

# 对差分后数据进行白噪声检验
from statsmodels.stats.diagnostic import acorr_ljungbox  # 对差分后达到平稳的数据进行白噪声检验

LjungBox = acorr_ljungbox(train_d1, lags=1)
print(LjungBox)# 发现序列是非白噪声序列

def evaluate():
    #建模并进行模型评价
    from statsmodels.tsa.arima.model import ARIMA
    # 这里我是通过pac和pacf图的拖尾来确定阶数
    model = ARIMA(train, order=(1,1,1))
    result = model.fit()
    result.summary()
    result.conf_int()
    resid = result.resid
    resid2= resid**2
    resid2.plot()
    plt.title("resid^2")
    plt.show()

    from statsmodels.graphics.tsaplots import plot_acf  # 导入自相关函数
    plot_acf(resid2, use_vlines=True, lags=30)
    plt.show()

    from statsmodels.graphics.tsaplots import plot_pacf  # 导入偏自相关函数
    plot_pacf(resid2, use_vlines=True, lags=30)
    plt.show()

    from arch import arch_model
    am = arch_model(resid)  # 默认模型为GARCH（1，1）
    model2 = am.fit(update_freq=0)  # 估计参数
    q=model2.forecast()
    qq=q.mean[-1:].values

    import scipy.stats as stats
    sm.ProbPlot(resid,stats.t,fit=True).ppplot(line='45')
    sm.ProbPlot(resid,stats.t,fit=True).qqplot(line='45')
    plt.show()






    #qqplot 基本在红线上，认为残差服从正态分布

#'''-------------------------------------------------------------------------------------------------
import numba
from numba import jit

#寻找阶数
#@jit
def find_piq(data=train):
    i = 0
    while True:
        data_di = data.diff(i).dropna()
        result = sm.tsa.stattools.adfuller(data_di)
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
            model = ARIMA(data,order=(p,i,q))
            result=model.fit()
            if result.bic <BIC:
                BIC=result.bic
                f_p=p
                f_q=q

    return(f_p,i,f_q)

#预测函数
#@jit
def arima_model(data=train):

    model = ARIMA(data, order=(1,1,1))#可以试着换成（1,1,1）
    result = model.fit()
    result.summary()
    result.conf_int()  # 系数显著
    forcast=result.forecast(30) #需要在这里改预测长度

    resid=result.resid
    #from arch import arch_model
    #am = arch_model(resid,dist='Normal')  # 默认模型为GARCH（1，1）
    #model2 = am.fit(update_freq=0)  # 估计参数
    #q = model2.forecast()
    #qq = int(q.mean[-1:].values)

    #forcast=forcast+qq



    return forcast

def draw(forcast_result,test):
    #画出图像进行比较
    date_index=pd.date_range('2021/7/1','2022/2/8')
    forcast_result = forcast_result.set_index(date_index)
    test=test.set_index(pd.date_range('2021/6/22','2022/2/8'))
    forcast_result.columns=['forcast_2']
    test.columns=['test']
    show_result=forcast_result.join(test[1:2])
    show_result.plot()
    plt.title("Premium Rate")  # 添加图标题
    plt.xticks(rotation=45)  # 横坐标旋转45度
    plt.xlabel('date')  # 添加图的标签（x轴，y轴）
    plt.ylabel('%')
    plt.show()




#预测结果分析
forcast_result=pd.DataFrame()
for i in range(203):
    data=gbtc_data_filled['discount rate'][i:539 + i]
    q=arima_model(data)
    q=pd.DataFrame(q)       #这个是为了多步预测的时候取最后一个数弄的
    forcast_result=forcast_result.append(pd.DataFrame(q[29:30]),ignore_index=True)
#draw(forcast_result*100,test*100)

#计算平均绝对误差
def average_abs_error():
    r1=test['discount rate'][29:].tolist()
    r2=forcast_result['predicted_mean'].tolist()
    r=list(map(lambda x: abs(x[0]-x[1]),zip(r1,r2)))
    average_abs_error=np.average(r)
    print(np.average(r))
    lose=0
    lose_sum=0
    win=0
    win_sum=0
    for i in range(len(r1)):
        if r1[i]<(r2[i]-0.01):
            lose = lose+1
            lose_sum = lose_sum + (r1[i] - r2[i])
            lose_average=lose_sum/lose
        else:
            win = win+1
            win_sum = win_sum +(r2[i]-r1[i])
            win_average= win_sum/win
    print(lose,lose_average,win,win_average,average_abs_error)
    return average_abs_error


average_abs_error()


