"""
 Created on 2022/5/6
 @author  : ivy
 @File    : order_info_push_without_cam.py
 @Description: 独立于cam系统的订单信息推送
"""

import pandas as pd
import psycopg2
import asyncio
import time
import json
import sys
from utils.ding_push import DingReporter
from get_info.get_price_4exchange import get_avg_price



class order_info_push_sql:
    def __init__(self,ding_bot,LB=[]):
        self.ding_bot = ding_bot
        self.LB=LB

    def connect_db(self, tablename, sql=None):
        conn = psycopg2.connect(database='', user='',
                                password='', host='', port=)

        # sql语句
        if not sql:
            sql = "select * from {}".format(tablename)
        df = pd.read_sql(sql=sql, con=conn)
        df=df.to_dict('index')
        return df
    #qq=connect_db('collateral_order_info')



    async def info_push(self):
        # 获取数据
        order_data=self.connect_db('collateral_order_info')
        print(order_data)

        #借入单
        result_text = "借入订单:\n"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))) + "\n"
        try:
            for i in order_data:
                if order_data[i]['borrower'] in self.LB:
                    #print(order_data[i])
                    if order_data[i]['collateral']=='':
                        ltv='无抵押'
                    else:
                        if order_data[i]['borrow']=='USDT':
                            borrow_price=1
                        else:
                            borrow_price=get_avg_price(order_data[i]['borrow'])
                        borrow=borrow_price*order_data[i]['borrow_amount']
                        #print(borrow)

                        if order_data[i]['collateral']=='USDT':
                            collateral_price=1
                        else:
                            collateral_price=get_avg_price(order_data[i]['collateral'])
                        collateral=collateral_price*order_data[i]['collateral_amount']

                        ltv=round(borrow/collateral*100,2)
                        #print(ltv)
                        end_date=str(order_data[i]['end_time']).split(' ')[0]

                    result_text += '{}的{}到期的质押{}借贷{}订单的实时LTV为{}%\n'.format(
                        order_data[i]['borrower'],
                        end_date,
                        str(order_data[i]['collateral_amount'])+order_data[i]['collateral'],
                        str(order_data[i]['borrow_amount'])+order_data[i]['borrow'],
                        ltv
                        )

        except:
            await self.ding_bot.send_alert("you meet problem : {}".format(Exception))
        await self.ding_bot.send(result_text)

        #借出单
        result_text = "借出订单:\n" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))) + "\n"
        try:
            for i in order_data:
                if order_data[i]['lender'] in self.LB:
                    # print(order_data[i])
                    if order_data[i]['collateral'] == '':
                        ltv = '无抵押'
                    else:
                        if order_data[i]['borrow'] == 'USDT':
                            borrow_price = 1
                        else:
                            borrow_price = get_avg_price(order_data[i]['borrow'])
                        borrow = borrow_price * order_data[i]['borrow_amount']
                        # print(borrow)

                        if order_data[i]['collateral'] == 'USDT':
                            collateral_price = 1
                        else:
                            collateral_price = get_avg_price(order_data[i]['collateral'])
                        collateral = collateral_price * order_data[i]['collateral_amount']

                        ltv = round(borrow / collateral * 100, 2)
                        # print(ltv)
                        end_date = str(order_data[i]['end_time']).split(' ')[0]

                    result_text += '{}的{}到期的质押{}借贷{}订单的实时LTV为{}%\n'.format(
                        order_data[i]['borrower'],
                        end_date,
                        str(order_data[i]['collateral_amount']) + order_data[i]['collateral'],
                        str(order_data[i]['borrow_amount']) + order_data[i]['borrow'],
                        ltv
                    )

        except:
            await self.ding_bot.send_alert("you meet problem : {}".format(Exception))
        await self.ding_bot.send(result_text)



        await asyncio.sleep(300)
        asyncio.ensure_future(self.info_push())

    def run(self):
        asyncio.ensure_future(self.info_push())
        asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    json_info = json.load(open("../ding.json"))
    dingding_bot_info = json_info['order_info']
    dingding = DingReporter(dingding_bot_info)

    bot = order_info_push_sql(dingding, LB=[" "," "])
    #根据borrower和lender的名字来判断是借出还是借入，当borrower在LB当就是借入订单
    bot.run()

