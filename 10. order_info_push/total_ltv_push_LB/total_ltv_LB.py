"""
 Created on 2022/4/28
 @author  : ivy
 @File    : total_ltv_LB.py
 @Description: 分别推送借贷方订单总体ltv信息
"""

import asyncio
import time
import aiohttp
import json
import sys

from typing import Tuple

sys.path.insert(0, '/home/strategy_dev/Libs/jingwei')

from utils.generate_header import generate_header
from utils.ding_push import DingReporter
from get_info.get_accrual import get_all_accrual
from get_info.get_accrual import get_price_usdt

class over_all_ltv_monitor:
    def __init__(self, ding_bot, api_key, secret_key, base_url, order_info_type='loan_id', info_list: Tuple = (),LB=[]):
        self.ding_bot = ding_bot
        self.base_url = base_url
        self.api_key = api_key
        self.secret_key = secret_key
        self.order_info_type = order_info_type
        self.info_list = info_list
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

    def _generate_path(self):
        base = "/otc-assets/broker/loan/batch-records?type="
        base += self.order_info_type + "&val="
        base += ",".join(self.info_list)
        return base

    async def overall_push(self):
        # 获取数据
        async with aiohttp.ClientSession() as session:
            timestamp = str(int(time.time()))
            async with session.get(
                    self.base_url+self._generate_path(),
                    headers=generate_header(
                        api_key=self.api_key, secret_key=self.secret_key,
                        base_url=self.base_url, path=self._generate_path()
                    ).gen_header(
                        path=self._generate_path(), time_stamp=timestamp
                    )) as response:
                result = await response.text()
                # 这里其实需要给 except 加上一个报警, 如果出现了信息中断的情况, 就应该@我
                try:
                    message = json.loads(result)
                    # await self.ding_bot.send(result)
                except Exception as e:
                    await self.ding_bot.send_alert('you meet problem: {}'.format(e))


                target_list_B={}
                target_list_L={}
                special={}


                print(message)
                try:
                    for key, value in message.items():
                        #value = value[0]
                        if value[0]['borrower'] in self.LB and value[0]['collateral']!='':
                            target_list_B[key]=value
                        if value[0]['lender'] in self.LB and value[0]['collateral']!='':
                            target_list_L[key]=value
                        if value[0]['collateral']=='':
                            special[key]=value

                except:
                    await self.ding_bot.send_alert("you meet problem : {}".format(message["message"]))

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
                        if target_list_B[i][0]['currency']=='usdt':
                             borrow_price=1
                        else:
                            borrow_price=float(await get_price_usdt(target_list_B[i][0]['currency']))
                        total_borrow += float(target_list_B[i][0]['amount'])*borrow_price

                    #算出所有的borrower的名单
                        if target_list_B[i][0]['borrower'] not in borrower:
                            borrower.append(target_list_B[i][0]['borrower'])
                    #算出总质押（usdt）
                        collateral_kv=target_list_B[i][0]['collateral'].split(' ')
                        if collateral_kv[-1]=='USDT':
                            collateral_price=1
                        else:
                            collateral_price=float(await get_price_usdt(collateral_kv[-1].lower()))
                        total_collateral += float(collateral_kv[0])*collateral_price
                    #算出总可支付利息
                        if target_list_B[i][0]['currency'] == 'usdt':
                            interest_price = 1
                        else:
                            interest_price = float(await get_price_usdt(target_list_B[i][0]['currency']))
                        total_payable_interest += float(target_list_B[i][0]['payable_interest']) * interest_price
                    #总ltv
                    total_ltv=total_borrow/total_collateral
                    result_text +='======================='

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
                # print(target_list)
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
                        if target_list_L[i][0]['currency'] == 'usdt':
                            borrow_price = 1
                        else:
                            borrow_price = float(await get_price_usdt(target_list_L[i][0]['currency']))
                        total_borrow += float(target_list_L[i][0]['amount']) * borrow_price

                        # 算出所有的borrower的名单
                        if target_list_L[i][0]['borrower'] not in borrower:
                            borrower.append(target_list_L[i][0]['borrower'])
                        # 算出总质押（usdt）
                        collateral_kv = target_list_L[i][0]['collateral'].split(' ')
                        if collateral_kv[-1] == 'USDT':
                            collateral_price = 1
                        else:
                            collateral_price = float(await get_price_usdt(collateral_kv[-1].lower()))
                        total_collateral += float(collateral_kv[0]) * collateral_price
                        # 算出总可支付利息
                        if target_list_L[i][0]['currency'] == 'usdt':
                            interest_price = 1
                        else:
                            interest_price = float(await get_price_usdt(target_list_L[i][0]['currency']))
                        total_payable_interest += float(target_list_L[i][0]['payable_interest']) * interest_price
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
                            special[i][0]['borrower'],
                            special[i][0]['end_date'],
                            special[i][0]['borrow'])


                    except:
                        await self.ding_bot.send_alert("you meet problem : {}".format(message["message"]))

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
    mode = 'production'
    id_tuple=tuple(get_all_accrual(mode=mode))#保证获取到订单列表的环境和推送的是一致的
    if mode == 'production':
        api = json_info['cam_api']['api']
        secret = json_info['cam_api']['secret']
        url = json_info['cam_base_url']['business_url']
        dingding_bot_info = json_info["total_ltv"]
    elif mode == 'test':
        api = json_info['test_cam_api']['api']
        secret = json_info['test_cam_api']['secret']
        url = json_info['cam_base_url']['test_url']
        dingding_bot_info = json_info["total_ltv"]
    else:
        raise Exception('please check you mode')
    dingding = DingReporter(dingding_bot_info)

    bot = over_all_ltv_monitor(dingding, api_key=api, secret_key=secret, base_url=url, info_list=id_tuple,LB=[" "," "])
    #根据borrower和lender的名字来判断是借出还是借入，当borrower在LB当就是借入订单
    bot.run()



