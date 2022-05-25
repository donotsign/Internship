from websocket import create_connection
import gzip
import json
import pandas as pd
import time
from datetime import datetime


def Huobi_kline(symbol, period='1min', client_id='huobi_id',
                start_time=None, end_time=None, is_fr=False,
                get_full_market_data=False, adjust_time=True,
                col_with_asset_name=True, get_adj=False):
    # 用来确定websocket行情请求地址
    if symbol[-2:] in {'CW', 'CQ', 'NW', 'NQ'}:
        ws_add = 'wss://api.hbdm.vn/ws'
        symbol_name = ''.join(symbol.split('_'))
    elif symbol[-3:] == 'USD':
        if is_fr:
            ws_add = 'wss://api.hbdm.vn/ws_index'
        else:
            ws_add = 'wss://api.hbdm.vn/swap-ws'
        symbol_name = symbol
    elif symbol[-4:] == 'USDT':
        if is_fr:
            ws_add = 'wss://api.hbdm.vn/ws_index'
        else:
            ws_add = 'wss://api.hbdm.vn/linear-swap-ws'
        symbol_name = symbol
    else:
        ws_add = "wss://api-aws.huobi.pro/ws"
        symbol_name = symbol

    # 用来进行循环取数
    time_interval = 60
    if period == '1min':
        time_interval = 60
    elif period == '5min':
        time_interval = 300
    elif period == '15min':
        time_interval = 900
    elif period == '30min':
        time_interval = 1800
    elif period == '60min':
        time_interval = 3600
    elif period == '4hour':
        time_interval = 14400
    elif period == '1day':
        time_interval = 86400

    if end_time == None:
        end_timestamp = int(datetime.timestamp(datetime.now()))
        end_timestamp -= end_timestamp % time_interval
    else:
        end_timestamp = end_time

    if start_time == None:
        start_timestamp = end_timestamp - 299 * time_interval
    else:
        start_timestamp = start_time

    iteration = (end_timestamp - start_timestamp)//(time_interval*300) + 1

    while True:
        try:
            ws = create_connection(ws_add)
            break
        except Exception as e:
            print(e)
            print(symbol+' connect ws error,retry...')
            time.sleep(2)

    if is_fr:
        result_data = pd.DataFrame(columns=['datetime', 'hbfr'+symbol_name+'_close'])
    else:
        if get_full_market_data:
            result_data = pd.DataFrame(columns=['datetime', 'hb'+symbol_name+'_open', 'hb'+symbol_name+'_high',
                                                'hb'+symbol_name+'_low', 'hb'+symbol_name+'_close',
                                                'hb'+symbol_name+'_volume', 'hb'+symbol_name+'_amount'])
        else:
            result_data = pd.DataFrame(columns=['datetime', 'hb'+symbol_name+'_close'])

    for i in range(iteration):
        interval_time = end_timestamp - 299 * time_interval
        if interval_time < start_timestamp:
            interval_time = start_timestamp
        if start_timestamp > end_timestamp:
            break
        if not is_fr:
            kline_request = json.dumps({"req": "market.{symbol}.kline.{period}".format(symbol=symbol, period=period),
                                        'id': str(client_id),
                                        "from": interval_time,
                                        "to": end_timestamp})
        else:
            kline_request = json.dumps({"req": "market.{symbol}.estimated_rate.{period}".format(symbol=symbol, period=period),
                                        'id': str(client_id),
                                        "from": interval_time,
                                        "to": end_timestamp})

        ws.send(kline_request)
        # break_signal = False
        while True:
            break_count = 0
            while True:
                try:
                    compressData = ws.recv()
                    break
                except Exception as e:
                    print(e)
                    print(symbol+' receive fail, retry...')
                    time.sleep(0.3)
                    break_count += 1
                    if break_count >= 10:
                        raise Exception('There may be some problems, please retry later.')
            result = gzip.decompress(compressData).decode('utf-8')
            if result[:7] == '{"ping"':
                ts = result[8:21]
                pong = '{"pong":'+ts+'}'
                ws.send(pong)
                end_timestamp = interval_time - time_interval
#             elif result[2:5] == 'err':
#                 raise Exception('get error!')
            else:
                result = json.loads(result)
                # try:
                if not result['data'] and result['status'] == 'ok':
                    break
                elif result['status'] != 'ok':
                    raise Exception('Got nothing. There may be some problems in symbol or start/end timestamp.')
                else:
                    if get_full_market_data:
                        if symbol[-4:] == 'USDT':
                            cache = pd.DataFrame(result['data'])[['id', 'open', 'high', 'low', 'close', 'trade_turnover', 'amount']].rename(columns={"trade_turnover": 'vol'})
                        else:
                            cache = pd.DataFrame(result["data"])[['id', 'open', 'high', 'low', 'close', 'vol', 'amount']]
                        if not is_fr:
                            cache = cache.rename(columns={'id': 'datetime', 'open': 'hb'+symbol_name+'_open', 'high': 'hb'+symbol_name+'_high',
                                                          'low': 'hb'+symbol_name+'_low', 'close': 'hb'+symbol_name+'_close',
                                                          'vol': 'hb'+symbol_name+'_volume', 'amount': 'hb'+symbol_name+'_amount'})
                        else:
                            cache = cache.rename(columns={'id': 'datetime', 'open': 'hbfr'+symbol_name+'_open',
                                                          'high': 'hbfr'+symbol_name+'_high', 'low': 'hbfr'+symbol_name+'_low',
                                                          'close': 'hbfr'+symbol_name+'_close', 'vol': 'hbfr'+symbol_name+'_volume',
                                                          'amount': 'hbfr'+symbol_name+'_amount'})
                    else:
                        cache = pd.DataFrame(result["data"])[['id', 'close']]
                        if not is_fr:
                            cache = cache.rename(columns={'id': 'datetime', 'close': 'hb'+symbol_name+'_close'})
                        else:
                            cache = cache.rename(columns={'id': 'datetime', 'close': 'hbfr'+symbol_name+'_close'})
                    result_data = result_data.append(cache)
                    end_timestamp = interval_time - time_interval
                    break
                # except Exception as e:
                #     print(e)
                #     print(symbol, result)

        # if break_signal:
        #     break

        time.sleep(0.5)

    result_data.sort_values('datetime', inplace=True)
    # 调整时间, 并且把时间列的格式改成datetime格式
    if adjust_time:
        result_data['datetime'] += 28800
        result_data['datetime'] = pd.to_datetime(result_data['datetime'], unit='s')
    result_data.reset_index(drop=True, inplace=True)
    for i in result_data.columns[1:]:
        result_data[i] = result_data[i].astype('float')
        
    result_data.set_index(['datetime'], inplace=True)
        
    if col_with_asset_name:
        return result_data
    else:
        rename_dict = {}
        for i in result_data.columns:
            rename_dict[i] = i.split("_")[-1]
        result_data.rename(columns=rename_dict, inplace=True)
        if get_adj:
            result_data['adj_close'] = result_data['close']
        # result_data.drop(['index'], axis=1, inplace=True)
        return result_data


if __name__ == '__main__':
    # start_time = int(time.mktime(time.strptime('2021-01-01 00:00:00', '%Y-%m-%d %H:%M:%S')))
    start_time = int(time.time()) - 365 * 86400
    period = '5min'
    target = 'woousdt'
    result_data = Huobi_kline(symbol=target, period=period, start_time=start_time, get_full_market_data=True, col_with_asset_name=False)
    # fil_data['per_1'] = (fil_data['high'] - fil_data['open']) / fil_data['open']
    # fil_data['per_2'] = (fil_data['close'] - fil_data['low']) / fil_data['low']
    # result = fil_data['per_1'].append(fil_data['per_2'])
    # print(result.describe(percentiles=[.25, .75, .8, .9, .95, .99]))
    result_data = pd.DataFrame(result_data)
    result_data.to_csv('../data/woo_huobi_spot.csv')
    # result_data['amount'] = result_data['volume'] * (result_data['high'] + result_data['low'] + result_data['close']) / 3
    # print("daily avg amount for woo in huobi is {}".format(result_data['amount'].mean()))
    # print("daily avg volume for woo in huobi is {}".format(result_data['volume'].mean()))
    # print("daily avg amount for woo in huobi in recent half year is {}".format(result_data.iloc[182:, 5].mean()))
    # print("daily avg volume for woo in huobi in recent half year is {}".format(result_data.iloc[182:, 4].mean()))
    # print("daily avg amount for woo in huobi in recent three months is {}".format(result_data.iloc[270:, 5].mean()))
    # print("daily avg volume for woo in huobi in recent three months is {}".format(result_data.iloc[270:, 4].mean()))
    print(result_data)

