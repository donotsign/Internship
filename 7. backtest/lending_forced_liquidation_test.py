"""
 Created on: 2022.3.18
 @author   : ivy
 @File     : lending_forced_liquidation_test
 @Description: 强平策略回测
"""

import datetime

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import datetime
#======================================================================================================================
#所有参数：
#======================================================================================================================
trans_cost=0.03/100  #交易费用
trade_limit=0.05  #平仓限制占总交易量%
borrow=10000000    #借款
customer_cap=5000000  #客户自有资金
init_cap=borrow+customer_cap
time_length=90
interest_rate=0.08  #全年利率0.08
interest_rate=interest_rate*time_length/360
tier1=['btcusdt', 'ethusdt']
tier2=['trxusdt', 'shibusdt', 'solusdt', 'dotusdt','filusdt', 'dogeusdt',
       'adausdt', 'linkusdt', 'sandusdt', 'ltcusdt','avaxusdt']
tier3=[ 'eosusdt', 'bchusdt', 'uniusdt', 'sushiusdt', 'aaveusdt',
        'etcusdt', 'crousdt', 'axsusdt', 'zecusdt', 'xlmusdt']
tier4=['bsvusdt', 'dashusdt', '1inchusdt', 'xmrusdt', 'compusdt',
        'iotausdt', 'sklusdt', 'paxusdt', 'wbtcusdt']
tier=[tier1,tier2,tier3,tier4]
all_coin=['btcusdt', 'ethusdt', 'trxusdt', 'shibusdt', 'solusdt', 'dotusdt',
              'filusdt', 'dogeusdt', 'adausdt', 'linkusdt', 'sandusdt', 'ltcusdt',
              'avaxusdt', 'eosusdt', 'bchusdt', 'uniusdt', 'sushiusdt', 'aaveusdt',
              'etcusdt', 'crousdt', 'axsusdt', 'zecusdt', 'xlmusdt', 'bsvusdt',
               'dashusdt', '1inchusdt', 'xmrusdt', 'compusdt','iotausdt', 'sklusdt', 'paxusdt', 'wbtcusdt']
#强平线
risk_rate_line1=1.1
risk_rate_line2=1.1
risk_rate_line3=1.1
risk_rate_line4=1.1
#滑点
slope1=0.03/100
slope2=0.06/100
slope3=0.08/100
slope4=0.1/100
slope=[slope1,slope2,slope3,slope4]

#读取数据
data={}
for i in all_coin:
    file='~data\\{}_5min_20210512_20220312.csv'.format(i)
    data[i]=pd.read_csv(file)
data_dict={}
for i in data:
    data_dict[i]=data[i].to_dict('index')
#------------------------------------------------------------------------------------------------------------------------
#=======================================================================================================================

#生成初始的资金分配
def get_random():
    tier_len1=len(tier1)
    tier_len2=len(tier2)
    tier_len3=len(tier3)
    tier_len4=len(tier4)
    w1=[]
    w2=[]
    w3=[]
    w4=[]
    w_total=[]
    for i in range(tier_len1):
        rand=np.random.randn()
        while rand<=0:
            rand=np.random.randn(1)
        w1.append(float(rand))

    for i in range(tier_len2):
        rand=np.random.randn(1)
        while rand<=0:
            rand=np.random.randn(1)
        w2.append(float(rand))

    for i in range(tier_len3):
        rand=np.random.randn(1)
        while rand<=0:
            rand=np.random.randn(1)
        w3.append(float(rand))

    for i in range(tier_len4):
        rand=np.random.randn(1)
        while rand<=0:
            rand=np.random.randn(1)
        w4.append(float(rand))

    #归一化处理
    w1=(np.array(w1)/sum(w1)*0.4).tolist()
    w2=(np.array(w2)/sum(w2)*0.3).tolist()
    w3=(np.array(w3)/sum(w3)*0.2).tolist()
    w4=(np.array(w4)/sum(w4)*0.1).tolist()

    w_total=w1+w2+w3+w4
    return w_total
#计算初始各币种数量和使用资金，数量精确到0.01
def init_port(x):
    w0=get_random()
    port={}
    for i in range(len(all_coin)):
        port[all_coin[i]]=w0[i]*init_cap
    init_cap_act=0
    #初始币种个数
    for i in port:
        open_begin=((data[i].iloc[x])['open']+(data[i].iloc[x])['close'])/2
        amount=port[i]/open_begin
        amount=round(amount,2)
        init_cap_act=init_cap_act+amount*open_begin
        port[i]=amount
    rest_cap=init_cap-init_cap_act
    return port, init_cap_act,rest_cap
#开始进行强平和回测





def test(date):
    port, init_cap_act,rest_cap=init_port(date*24*12)
    trade_cost=0
    #先检查一下是不是数据都是全的
    size0=data[all_coin[0]].shape[0]
    for i in all_coin:
        size1=data[i].shape[0]
        if size0!=size1:
            raise Exception('data size in not constant!')
    #开始回测
    #当出发到各个强平线，line值由0变为1
    line=[0,0,0,0]

    data_size=size0
    risk_rate_list=[]
    for i in range(date*24*12,(date+time_length)*24*12,1):
        current_cap=0
        for m in port:
            #m='btcusdt'
            #open = (data[m].iloc[0])['open']
            open = data_dict[m][i]['open']
            current_cap=current_cap+open*port[m]
        risk_rate=(current_cap+rest_cap)/(borrow*(1+interest_rate))
        #print(risk_rate)
        risk_rate_list.append(risk_rate)
        #检查是否触发强平，如果已经触及就算升回来也要卖掉
        if risk_rate<=risk_rate_line1:
           # print('触发第一条线')
            line[0]=1
            if risk_rate<=risk_rate_line2:
                line[1]=1
              #  print('触发第二条线')
                if risk_rate<=risk_rate_line3:
                    line[2]=1
                #    print('触发第三条线')
                    if risk_rate<=risk_rate_line4:
                        line[3]=1
                #        print('触发第四条线')

        for n in range(len(line)):
            if line[n]==1:
                higest_sell={}
                sell_amount={}
                sell_price={}
                for j in tier[n]:
                    #higest_sell[j]=data[j].iloc[i]['amount']*trade_limit
                    higest_sell[j] = data_dict[j][i]['amount'] * trade_limit
                for k in higest_sell:
                    if higest_sell[k]<=port[k]: #如果超出卖出限制，就先卖限制量
                        sell_amount[k]=higest_sell[k]
                    else:#否则全部卖出
                        sell_amount[k]=port[k]
                    port[k]=port[k]-sell_amount[k]
                for l in tier[n]:
                    #sell_price[l]=(data[l].iloc[i]['open']+data[l].iloc[i]['close'])/2
                    sell_price[l] = (data_dict[l][i]['open'] + data_dict[l][i]['close']) / 2
                    rest_cap=rest_cap+sell_price[l]*sell_amount[l]*(1-trans_cost)*(1-slope[n])
                    trade_cost=trade_cost+sell_price[l]*sell_amount[l]*(1-(1-trans_cost)*(1-slope[n]))


    last_cap=current_cap+rest_cap



    return last_cap,risk_rate_list,trade_cost

def draw(risk_rate_list,date):
    time_x=data['btcusdt']['datetime'].tolist()
    for i in range(len(time_x)):
        time_x[i]=datetime.datetime.strptime(time_x[i],'%Y-%m-%d %H:%M:%S')
    plt.plot(time_x[date*24*12:(date+time_length)*24*12],risk_rate_list)
    plt.grid(linestyle='-.')
    plt.title('change of risk_rate')
    plt.xlabel("date")
    plt.ylabel("risk rate")
    plt.show()




if __name__ == '__main__':
    result_list=[]
    cost_list=[]
    # 此处的参数分别为0，30，60，90,120.....对应不同的开始天数
    date=210
    for test_num in range(30):
        result,rest_rate_list,trade_cost=test(date)
       # print('从第',date,'天开始，半年后最终总资产为： ', round(result,2))
        print(round(result,2))
        #print(round(trade_cost,2))
        result_list.append(round(result,2))
        cost_list.append(round(trade_cost,2))
    
    print('avg',np.mean(result_list))
    print('std',np.std(result_list))
    draw(rest_rate_list,date)
    df = pd.DataFrame(list(zip(result_list, cost_list)), columns=['result', 'cost'])
    df.to_csv('result.csv')





