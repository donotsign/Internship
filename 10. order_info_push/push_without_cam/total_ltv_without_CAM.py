"""
 Created on 2022/5/8
 @author  : ivy
 @File    : total_ltv_without_CAM.py
 @Description: 独立于cam系统的订单总体ltv信息推送
"""

import asyncio
import time
import datetime
import json
import sys
import psycopg2
import pandas as pd
from utils.ding_push import DingReporter
from get_info.get_price_4exchange import get_avg_price



from typing import Tuple




class over_all_ltv_monitor:
    def __init__(self, ding_bot, LB=[]):
        self.ding_bot = ding_bot
        self.LB=LB
        self.ltv_line_list = [0.9, 0.95, 1]


        self.normal_count_B = -1
        self.normal_count_L = -1
        self.normal_count_S = -1
        self.normal_push_min_interval = 5



        self.warning_trigger_B = False
        self.critical_trigger_B = False
        self.warning_trigger_L = False
        self.critical_trigger_L = False

    def connect_db(self, tablename, sql=None):
        conn = psycopg2.connect(database=' ', user=' ',
                                password=' ', host=' ', port= )

        # sql语句
        if not sql:
            sql = "select * from {}".format(tablename)
        df = pd.read_sql(sql=sql, con=conn)
        df=df.to_dict('index')
        return df


    #当前利息计算方式
    def calculate_interest(self,interest,interest_price,borrow_amount,days):
        return float(interest) * interest_price * borrow_amount * days / 365

    async def overall_push(self):
        # 获取数据
        order_data = self.connect_db('collateral_order_info')
        print(order_data)


        target_list_B={}
        target_list_L={}
        special={}
        try:
            for i in order_data:
                if order_data[i]['borrower'] in self.LB and order_data[i]['collateral']!='':
                    target_list_B[i]=order_data[i]
                if order_data[i]['lender'] in self.LB and order_data[i]['collateral']!='':
                    target_list_L[i]=order_data[i]
                if order_data[i]['collateral']=='':
                    special[i]=order_data[i]

        except :
            await self.ding_bot.send_alert("you meet problem : can't get target list")

        # 借入单
        result_text = "借入订单总ltv:\n" + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time()))) + "\n"
        count_amount_target=len(target_list_B)

        total_borrow=0
        total_collateral=0
        total_payable_interest=0
        borrower=[]

        if target_list_B == {}:
            result_text += 'No order'
            if self.normal_count_B == self.normal_push_min_interval or self.normal_count_B == -1:
                await self.ding_bot.send(result_text)
                self.normal_count_B = 0
            else:
                self.normal_count_B += 1

        else:
            #遍历list中的每一笔订单
            for i in target_list_B:

            #算出总借款（usdt）
                if target_list_B[i]['borrow']=='USDT':
                     borrow_price=1
                else:
                    borrow_price=get_avg_price(target_list_B[i]['borrow'])
                total_borrow += borrow_price*target_list_B[i]['borrow_amount']

            #算出所有的borrower的名单
                if target_list_B[i]['borrower'] not in borrower:
                    borrower.append(target_list_B[i]['borrower'])
            #算出总质押（usdt）
                collateral_kv=target_list_B[i]['collateral']
                if collateral_kv=='USDT':
                    collateral_price=1
                else:
                    collateral_price = get_avg_price(target_list_B[i]['collateral'])
                total_collateral += collateral_price * target_list_B[i]['collateral_amount']
            #算出目前产生利息
                #print(target_list_B[i]['start_time'])
                start=str(target_list_B[i]['start_time']).split(' ')[0]
                start=datetime.datetime.strptime(start,'%Y-%m-%d')
                time_interval=datetime.datetime.today()-start
                days=time_interval.days
                if target_list_B[i]['borrow'] == 'USDT':
                    interest_price = 1
                else:
                    interest_price = get_avg_price(target_list_B[i]['borrow'])
                #需要修改利息计算方式请在上方方程里面修改
                total_payable_interest += self.calculate_interest(target_list_B[i]['interest'],
                                                                  interest_price,target_list_B[i]['borrow_amount'],days)
            #总ltv
            total_ltv=total_borrow/total_collateral
            result_text +='======================='
#5.5做到这里
            if total_ltv < self.ltv_line_list[0]:
                 # 有一个推送间隔, 先定5min
                result_text += "{}: {}\n".format("存续中订单总量",count_amount_target )
                result_text += "{}: {}\n".format("用户总量", len(borrower))
                result_text += "{}: {}\n".format("抵押品当前总值",total_collateral )
                result_text += "{}: {}\n".format("贷出总值", total_borrow)
                result_text += "{}: {}\n".format("净资产总价值", total_collateral-total_borrow)
                result_text += "{}: {}\n".format("总 LTV", total_ltv)
                result_text += "{}: {}\n".format("已产生利息", total_payable_interest)
                status_B = "normal"
            elif total_ltv < self.ltv_line_list[1]:
                # 这里要@少数人
                result_text += "当前总LTV为{}%, 请注意提醒用户补仓并做好风控措施".format(total_ltv * 100)
                status_B = "warning"
            elif total_ltv < self.ltv_line_list[2]:
                # 这里要@所有人
                result_text += "当前总LTV为{}%, 面临较高风险, 请及时处理".format(total_ltv * 100)
                status_B = "critical"
            else:
                result_text += "当前总LTV为{}%, 风险极高, 请马上处理".format(total_ltv * 100)
                status_B = "critical"

            if status_B == "normal":
                if self.normal_count_B == self.normal_push_min_interval or self.normal_count_B == -1:
                    if self.warning_trigger_B:
                        result_text += "\n风险已经解除.\n"
                        self.warning_trigger_B = False
                        self.critical_trigger_B = False
                        await self.ding_bot.send_alert(result_text, is_at_all=True)
                    else:
                        await self.ding_bot.send(result_text)
                    self.normal_count_B = 0
                else:
                    self.normal_count_B += 1
            elif status_B == "warning":
                if self.warning_trigger_B:
                    await self.ding_bot.send(result_text)
                else:
                    await self.ding_bot.send_alert(result_text)
                    self.warning_trigger_B = True
                self.normal_count_B = 0
            elif status_B == "critical":
                if not self.critical_trigger_B:
                    await self.ding_bot.send_alert(result_text, is_at_all=True)
                    self.critical_trigger_B = True
                else:
                    await self.ding_bot.send(result_text)
                self.normal_count_B = 0


        #借出订单
        result_text = "借出订单总ltv:\n" + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time()))) + "\n"

        count_amount_target = len(target_list_L)

        total_borrow = 0
        count_amount = 0
        total_collateral = 0
        total_payable_interest=0
        borrower = []
        if target_list_L == {}:
            result_text += 'No order'
            if self.normal_count_L == self.normal_push_min_interval or self.normal_count_L == -1:
                await self.ding_bot.send(result_text)
                self.normal_count_L = 0
            else:
                self.normal_count_L += 1

        else:
            # 遍历list中的每一笔订单
            for i in target_list_L:

                # 算出总借款（usdt）
                if target_list_L[i]['borrow'] == 'USDT':
                    borrow_price = 1
                else:
                    borrow_price = get_avg_price(target_list_L[i]['borrow'])
                total_borrow += float(target_list_L[i]['borrow_amount']) * borrow_price

                # 算出所有的borrower的名单
                if target_list_L[i]['borrower'] not in borrower:
                    borrower.append(target_list_L[i]['borrower'])

                # 算出总质押（usdt）
                collateral_kv = target_list_L[i]['collateral']
                if collateral_kv == 'USDT':
                    collateral_price = 1
                else:
                    collateral_price = get_avg_price(collateral_kv)
                total_collateral += target_list_L[i]['collateral_amount'] * collateral_price

                # 算出总可支付利息
                #print(target_list_L[i]['start_time'])
                start = str(target_list_L[i]['start_time']).split(' ')[0]
                start = datetime.datetime.strptime(start, '%Y-%m-%d')
                time_interval = datetime.datetime.today() - start
                days = time_interval.days
                if target_list_L[i]['borrow'] == 'USDT':
                    interest_price = 1
                else:
                    interest_price = get_avg_price(target_list_L[i]['borrow'])
                # 需要修改利息计算方式请在上方方程里面修改！
                total_payable_interest += self.calculate_interest(target_list_L[i]['interest'],
                                                                  interest_price, target_list_L[i]['borrow_amount'],
                                                                  days)
            #算出总ltv
            total_ltv = total_borrow / total_collateral
            #total_ltv = 0.99
            result_text += '======================='

            if total_ltv < self.ltv_line_list[0]:
                # 有一个推送间隔, 先定5min
                result_text += "{}: {}\n".format("存续中订单总量", count_amount_target)
                result_text += "{}: {}\n".format("用户总量", len(borrower))
                result_text += "{}: {}\n".format("抵押品当前总值", total_collateral)
                result_text += "{}: {}\n".format("贷出总值", total_borrow)
                result_text += "{}: {}\n".format("净资产总价值", total_collateral - total_borrow)
                result_text += "{}: {}\n".format("总 LTV", total_ltv)
                result_text += "{}: {}\n".format("已产生利息", total_payable_interest)
                status_L = "normal"
            elif total_ltv < self.ltv_line_list[1]:
                # 这里要@少数人
                result_text += "当前总LTV为{}%, 请注意提醒用户补仓并做好风控措施".format(total_ltv * 100)
                status_L = "warning"
            elif total_ltv < self.ltv_line_list[2]:
                # 这里要@所有人
                result_text += "当前总LTV为{}%, 面临较高风险, 请及时处理".format(total_ltv * 100)
                status_L = "critical"
            else:
                result_text += "当前总LTV为{}%, 风险极高, 请马上处理".format(total_ltv * 100)
                status_L = "critical"
            #print(result_text)


            if status_L == "normal":
                if self.normal_count_L == self.normal_push_min_interval or self.normal_count_L == -1:
                    if self.warning_trigger_L:
                        result_text += "\n风险已经解除.\n"
                        self.warning_trigger_L = False
                        self.critical_trigger_L = False
                        await self.ding_bot.send_alert(result_text, is_at_all=True)
                    else:
                        await self.ding_bot.send(result_text)
                    self.normal_count_L = 0
                else:
                    self.normal_count_L += 1
            elif status_L == "warning":
                if self.warning_trigger_L:
                    await self.ding_bot.send(result_text)
                else:
                    await self.ding_bot.send_alert(result_text)
                    self.warning_trigger_L = True
                self.normal_count_L = 0
            elif status_L == "critical":
                if not self.critical_trigger_L:
                    await self.ding_bot.send_alert(result_text, is_at_all=True)
                    self.critical_trigger_L = True
                else:
                    await self.ding_bot.send(result_text)
                self.normal_count_L = 0

        #特殊情况
        result_text = "无抵押订单:\n" + time.strftime("%Y-%m-%d %H:%M:%S",time.localtime(int(time.time()))) + "\n"
        #print(special)
        if special == {}:
            result_text += 'No order'
            if self.normal_count_S == self.normal_push_min_interval or self.normal_count_S == -1:
                await self.ding_bot.send(result_text)
                self.normal_count_S = 0
            else:
                self.normal_count_S += 1
        else:

            try:
                for i in special:
                    result_text += '{}的{}到期的无抵押借贷{}订单\n'.format(
                    special[i]['borrower'],
                    str(special[i]['end_time']).split(' ')[0],
                    str(special[i]['borrow_amount'])+str(special[i]['borrow']))


            except:
                await self.ding_bot.send_alert("you meet problem : {}".format('error in special list'))

            if self.normal_count_S == self.normal_push_min_interval or self.normal_count_S == -1:
                await self.ding_bot.send(result_text)
                self.normal_count_S = 0
            else:
                self.normal_count_S += 1



        await asyncio.sleep(60)
        asyncio.ensure_future(self.overall_push())

    def run(self):
        asyncio.ensure_future(self.overall_push())
        asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    json_info = json.load(open("../ding.json"))
    dingding_bot_info = json_info["total_ltv"]
    dingding = DingReporter(dingding_bot_info)

    bot = over_all_ltv_monitor(dingding, LB=[" "," "])
    #根据borrower和lender的名字来判断是借出还是借入，当borrower在LB当就是借入订单
    bot.run()



