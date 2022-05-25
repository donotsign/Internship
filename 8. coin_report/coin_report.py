"""
 Created on 2022/4/21
 @author  : ivy
 @File    : coin_report.py
 @Description: 单币种分析
"""

import pandas as pd
import time
from get_data import Huobi_kline
import prettytable as pt
from rest_utils import api_key_get_hb
from decimal import Decimal
#from huobi_data_final import Huobi_kline


#-------------------参数--------------------------------
#coin='btcusdt'
#end = time.mktime(time.strptime("2022-03-12 00:00:00", "%Y-%m-%d %H:%M:%S"))
#start=time.mktime(time.strptime("2021-05-12 00:00:00", "%Y-%m-%d %H:%M:%S"))



def coin_analyse(coin,start=0,end=0):
    coin='btcusdt'
    end = int(time.mktime(time.strptime("2022-03-12 00:00:00", "%Y-%m-%d %H:%M:%S")))
    start = int(time.mktime(time.strptime("2022-02-12 00:00:00", "%Y-%m-%d %H:%M:%S")))
    end_fr=int(time.time())
    start_fr=int(end_fr-86400*360)
    #获取现货数据
    data_spot=Huobi_kline(symbol=coin, period='5min', start_time=start, end_time=end, get_full_market_data=True, col_with_asset_name=False)
    #获取U本位永续合约数据
    u=coin[:-4].upper()+'-USDT'
    data_U=Huobi_kline(symbol=u, period='5min', start_time=start, end_time=end, get_full_market_data=True, col_with_asset_name=False)
    u_fr=Huobi_kline(symbol=u, period='4hour', start_time=start_fr, end_time=end_fr, is_fr=True, get_full_market_data=True, col_with_asset_name=False)
    #获取币本位永续合约数据
    b=coin[:-4].upper()+'-USD'
    data_B=Huobi_kline(symbol=b, period='5min', start_time=start, end_time=end, get_full_market_data=True, col_with_asset_name=False)
    b_fr=Huobi_kline(symbol=b, period='4hour', start_time=start_fr, end_time=end_fr, is_fr=True,get_full_market_data=True, col_with_asset_name=False)


    def rsample(df,period):
        df_sample = pd.DataFrame()
        df_sample['open'] = df['open'].resample(period).first()
        df_sample['close'] = df['close'].resample(period).last()
        df_sample['high'] = df['high'].resample(period).max()
        df_sample['low'] = df['low'].resample(period).min()
        df_sample['volume'] = df['volume'].resample(period).sum()
        df_sample['money'] = df['amount'].resample(period).sum()
        print(df_sample)
        return df_sample
    #对现货分别取出不同频率的数据
    data_spot_15m=rsample(data_spot,'15min')
    data_spot_30m=rsample(data_spot,'30min')
    data_spot_1h=rsample(data_spot,'1h')
    data_spot_4h=rsample(data_spot,'4h')
    data_spot_1d = rsample(data_spot, '1d')
    #对U本位永续分别取不同频率
    data_U_15m = rsample(data_U, '15min')
    data_U_30m = rsample(data_U, '30min')
    data_U_1h = rsample(data_U, '1h')
    data_U_4h = rsample(data_U, '4h')
    data_U_1d = rsample(data_U, '1d')
    #对币本位永续分别取不同频率
    data_B_15m = rsample(data_B, '15min')
    data_B_30m = rsample(data_B, '30min')
    data_B_1h = rsample(data_B, '1h')
    data_B_4h = rsample(data_B, '4h')
    data_B_1d = rsample(data_B, '1d')

    U=[data_U,data_U_15m,data_U_30m,data_U_1h,data_U_4h,data_U_1d]
    B=[data_B,data_B_15m,data_B_30m,data_B_1h,data_B_4h,data_B_1d]

    def get_table(df):
        tb = pt.PrettyTable()
        tb.add_column('data', df.index)
        for col in df.columns.values:  # df.columns.values的意思是获取列的名称
            tb.add_column(col, df[col])
        return tb

    #取出8:00,14:00和24:00的费率
    fr_index=u_fr.index
    for i in fr_index:
        if i.hour in [0,8,16] :
            start=i
            break
    u_fr_data=u_fr.loc[start::2]

    fr_index = b_fr.index
    for i in fr_index:
        if i.hour in [0, 8, 16] :
            start = i
            break
    b_fr_data = b_fr.loc[start::2]

    u_fr_1w = Decimal(sum(u_fr_data['close'].iloc[:3*7])).quantize(Decimal("0.00000000"))
    u_fr_1m = Decimal(sum(u_fr_data['close'].iloc[:3*30])).quantize(Decimal("0.00000000"))
    u_fr_3m = Decimal(sum(u_fr_data['close'].iloc[:3*90])).quantize(Decimal("0.00000000"))
    u_fr_6m = Decimal(sum(u_fr_data['close'].iloc[:3*180])).quantize(Decimal("0.00000000"))
    u_fr_1y = Decimal(sum(u_fr_data['close'])).quantize(Decimal("0.00000000"))

    b_fr_1w = Decimal(sum(b_fr_data['close'].iloc[:3 * 7])).quantize(Decimal("0.00000000"))
    b_fr_1m = Decimal(sum(b_fr_data['close'].iloc[:3 * 30])).quantize(Decimal("0.00000000"))
    b_fr_3m = Decimal(sum(b_fr_data['close'].iloc[:3 * 90])).quantize(Decimal("0.00000000"))
    b_fr_6m = Decimal(sum(b_fr_data['close'].iloc[:3 * 180])).quantize(Decimal("0.00000000"))
    b_fr_1y = Decimal(sum(b_fr_data['close'])).quantize(Decimal("0.00000000"))

    u_fr_table={'时长':['1week','1month','3month','6month','1year'],'U本位合约费率加总':[u_fr_1w,u_fr_1m,u_fr_3m,u_fr_6m,u_fr_1y]}
    u_fr_table=pd.DataFrame(u_fr_table)
    u_fr_table.set_index(['时长'],inplace=True)

    b_fr_table = {'时长': ['1week', '1month', '3month', '6month', '1year'],'币本位合约费率加总': [b_fr_1w, b_fr_1m, b_fr_3m, b_fr_6m, b_fr_1y]}
    b_fr_table = pd.DataFrame(b_fr_table)
    b_fr_table.set_index(['时长'], inplace=True)

    u_fr_table=get_table(u_fr_table)
    b_fr_table=get_table(b_fr_table)

    #计算合约溢价率
    #合约溢价率
    def get_premium(spot,u,b):
        premium=pd.concat([spot['close'],u['close'],b['close']],axis=1)
        premium.columns=['spot','u_close','b_close']
        premium['premium_U']=(premium['u_close']-premium['spot'])/premium['spot']*10000
        premium['premium_B']=(premium['b_close']-premium['spot'])/premium['spot']*10000
        return premium
    premium_5min=get_premium(data_spot,data_U,data_B)
    premium_15min=get_premium(data_spot_15m,data_U_15m,data_B_15m)
    premium_30min =get_premium(data_spot_30m,data_U_30m,data_B_30m)
    premium_1h = get_premium(data_spot_1h,data_U_1h,data_B_1h)
    premium_4h = get_premium(data_spot_4h,data_U_4h,data_B_4h)
    premium_1d = get_premium(data_spot_1d,data_U_1d,data_B_1d)

    #现货描述统计
    def get_df(data):
        data['change_oc']=(data['close']-data['open'])/data['open']
        data['change_hl']=(data['high']-data['low'])/data['low']
        target_data=data
        target_data=target_data.drop(labels=['close','open','high','low'],axis=1)
        return target_data

    data_spot=get_df(data_spot)
    data_spot_15m=get_df(data_spot_15m)
    data_spot_30m=get_df(data_spot_30m)
    data_spot_1h=get_df(data_spot_1h)
    data_spot_4h=get_df(data_spot_4h)
    data_spot_1d=get_df(data_spot_1d)


    des_s_5min=data_spot.describe(percentiles=[0.05,0.25,0.5,0.75,0.95])
    des_s_15min=data_spot_15m.describe(percentiles=[0.05,0.25,0.5,0.75,0.95])
    des_s_30min=data_spot_30m.describe(percentiles=[0.05,0.25,0.5,0.75,0.95])
    des_s_1h=data_spot_1h.describe(percentiles=[0.05,0.25,0.5,0.75,0.95])
    des_s_4h=data_spot_4h.describe(percentiles=[0.05,0.25,0.5,0.75,0.95])
    des_s_1d=data_spot_1d.describe(percentiles=[0.05,0.25,0.5,0.75,0.95])

    #合约描述统计
    #data_U_1=pd.concat([data_U,premium_5min['premium_U']],axis=1)

    data_U=get_df(data_U)
    data_U_15m=get_df(data_U_15m)
    data_U_30m=get_df(data_U_30m)
    data_U_1h=get_df(data_U_1h)
    data_U_4h=get_df(data_U_4h)
    data_U_1d=get_df(data_U_1d)

    data_U = pd.concat([data_U, premium_5min['premium_U']], axis=1)
    data_U_15m = pd.concat([data_U_15m, premium_15min['premium_U']], axis=1)
    data_U_30m = pd.concat([data_U_30m, premium_30min['premium_U']], axis=1)
    data_U_1h = pd.concat([data_U_1h, premium_1h['premium_U']], axis=1)
    data_U_4h = pd.concat([data_U_4h, premium_4h['premium_U']], axis=1)
    data_U_1d = pd.concat([data_U_1d, premium_1d['premium_U']], axis=1)

    des_u_5min = data_U.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_u_15min = data_U_15m.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_u_30min = data_U_30m.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_u_1h = data_U_1h.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_u_4h = data_U_4h.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_u_1d = data_U_1d.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])

    data_B = get_df(data_B)
    data_B_15m = get_df(data_B_15m)
    data_B_30m = get_df(data_B_30m)
    data_B_1h = get_df(data_B_1h)
    data_B_4h = get_df(data_B_4h)
    data_B_1d = get_df(data_B_1d)

    data_B = pd.concat([data_B, premium_5min['premium_B']], axis=1)
    data_B_15m = pd.concat([data_B_15m, premium_15min['premium_B']], axis=1)
    data_B_30m = pd.concat([data_B_30m, premium_30min['premium_B']], axis=1)
    data_B_1h = pd.concat([data_B_1h, premium_1h['premium_B']], axis=1)
    data_B_4h = pd.concat([data_B_4h, premium_4h['premium_B']], axis=1)
    data_B_1d = pd.concat([data_B_1d, premium_1d['premium_B']], axis=1)

    des_b_5min = data_B.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_b_15min = data_B_15m.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_b_30min = data_B_30m.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_b_1h = data_B_1h.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_b_4h = data_B_4h.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])
    des_b_1d = data_B_1d.describe(percentiles=[0.05, 0.25, 0.5, 0.75, 0.95])







    table_s_5min=get_table(des_s_5min)
    table_s_15min=get_table(des_s_15min)
    table_s_30min=get_table(des_s_30min)
    table_s_1h=get_table(des_s_1h)
    table_s_4h=get_table(des_s_4h)
    table_s_1d=get_table(des_s_1d)

    table_u_5min = get_table(des_u_5min)
    table_u_15min = get_table(des_u_15min)
    table_u_30min = get_table(des_u_30min)
    table_u_1h = get_table(des_u_1h)
    table_u_4h = get_table(des_u_4h)
    table_u_1d = get_table(des_u_1d)

    table_b_5min = get_table(des_b_5min)
    table_b_15min = get_table(des_b_15min)
    table_b_30min = get_table(des_b_30min)
    table_b_1h = get_table(des_b_1h)
    table_b_4h = get_table(des_b_4h)
    table_b_1d = get_table(des_b_1d)

    api_config = {'api':'*****','secret':'******'}


    #合约创建时间
    def get_creat_date(api_config, symbol):
        futures_url = 'https://api.hbdm.com'
        if symbol[-4:] == 'USDT':
            curl = '/linear-swap-api/v1/swap_contract_info'
        elif symbol[-3:] == 'USD':
            curl = '/swap-api/v1/swap_contract_info'

        res = api_key_get_hb(futures_url, curl, {'contract_code': symbol}, api_config['api'], api_config['secret'])
        return res.get('data')[0].get('create_date')

    create_u=get_creat_date(api_config,u)
    create_b=get_creat_date(api_config,b)
    data={'{}合约上市时间'.format(u):[create_u],'{}合约上市时间'.format(b):[create_b]}
    create_date=pd.DataFrame(data)
    create_date=get_table(create_date)

    #往文件里写结果
    f=open('{}_report.txt'.format(coin),'w')
    f.write('{}币种分析报告\n'.format(coin))
    f.write('参数解释:\n')
    f.write('count:数据数量     \nmean:平均值    \nstd:标准差     \nmin:最小值   \nn%:n%的分位数   \nmax:最大值\n')
    f.write('volume:交易额     \nmoney/amount:交易量\n'
            'change_oc=(close-open)/open  通过开盘收盘价计算的价格波动率\n'
            'change_hl=(high-low)/low     通过最高最低价计算价格波动率\n'
            'premium_U:U本位合约溢价率*100\n'
            'premium_B:币本位合约溢价率*100\n'
            )
    f.write('\n')
    f.write('频数为5min的数据分析结果：\n')
    f.write('现货:\n')
    f.write(str(table_s_5min))
    f.write('\nU本位合约\n')
    f.write(str(table_u_5min))
    f.write('\n币本位合约\n')
    f.write(str(table_b_5min))
    f.write('\n\n')
    f.write('频数为15min的数据分析结果：\n')
    f.write('现货:\n')
    f.write(str(table_s_15min))
    f.write('\nU本位合约\n')
    f.write(str(table_u_15min))
    f.write('\n币本位合约\n')
    f.write(str(table_b_15min))
    f.write('\n\n')
    f.write('频数为30min的数据分析结果：\n')
    f.write('现货:\n')
    f.write(str(table_s_30min))
    f.write('\nU本位合约\n')
    f.write(str(table_u_30min))
    f.write('\n币本位合约\n')
    f.write(str(table_b_30min))
    f.write('\n\n')
    f.write('频数为1h的数据分析结果：\n')
    f.write('现货:\n')
    f.write(str(table_s_1h))
    f.write('\nU本位合约\n')
    f.write(str(table_u_1h))
    f.write('\n币本位合约\n')
    f.write(str(table_b_1h))
    f.write('\n\n')
    f.write('频数为4h的数据分析结果：\n')
    f.write('现货:\n')
    f.write(str(table_s_4h))
    f.write('\nU本位合约\n')
    f.write(str(table_u_4h))
    f.write('\n币本位合约\n')
    f.write(str(table_b_4h))
    f.write('\n\n')
    f.write('频数为1d的数据分析结果：\n')
    f.write('现货:\n')
    f.write(str(table_s_1d))
    f.write('\nU本位合约\n')
    f.write(str(table_u_1d))
    f.write('\n币本位合约\n')
    f.write(str(table_b_1d))
    f.write('\n\n\n')
    f.write('合约上市时间为:\n')
    f.write(str(create_date))
    f.write('\n\nU本位合约资金费率加总：\n')
    f.write(str(u_fr_table))
    f.write('\n币本位合约资金费率加总：\n')
    f.write(str(b_fr_table))

    f.close()

# 按间距中的绿色按钮以运行脚本。
if __name__ == '__main__':
    coin='dogeusdt'
    end = int(time.mktime(time.strptime("2022-03-12 00:00:00", "%Y-%m-%d %H:%M:%S")))
    start = int(time.mktime(time.strptime("2022-02-12 00:00:00", "%Y-%m-%d %H:%M:%S")))
    coin_analyse(coin=coin,start=start,end=end)

# 访问 https://www.jetbrains.com/help/pycharm/ 获取 PyCharm 帮助
