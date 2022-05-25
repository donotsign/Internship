"""
 Created on 2022/4/20
 @author  : ivy
 @File    : order_info_push_LB.py
 @Description: 借方和贷方订单信息分别推送
"""
import asyncio
import time
import aiohttp
import json
import sys
from typing import Tuple


from utils.generate_header import generate_header
from utils.ding_push import DingReporter
from get_info.get_accrual import get_all_accrual


class order_info_push:
    def __init__(self, ding_bot, api_key, secret_key, base_url, order_info_type='loan_id', info_list: Tuple = (),LB=[]):
        self.ding_bot = ding_bot
        self.base_url = base_url
        self.api_key = api_key
        self.secret_key = secret_key
        self.order_info_type = order_info_type
        self.info_list = info_list
        self.LB=LB

    def _generate_path(self):
        base = "/otc-assets/broker/loan/batch-records?type="
        base += self.order_info_type + "&val="
        base += ",".join(self.info_list)
        return base

    async def info_push(self):
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
                #借入单
                result_text = "借入订单:\n"+time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))) + "\n"
                try:
                    for key, value in message.items():
                        value = value[0]
                        if value['borrower'] in self.LB:
                            result_text += '{}的{}到期的质押{}借贷{}订单的实时LTV为{}%\n'.format(
                                value['borrower'],
                                value['end_date'],
                                value['collateral'],
                                value['borrow'],
                                round(float(value['ltv']) * 100, 2)
                            )

                except:
                    await self.ding_bot.send_alert("you meet problem : {}".format(message["message"]))
                await self.ding_bot.send(result_text)
                #借出单
                result_text = "借出订单:\n" + time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(int(time.time()))) + "\n"
                try:
                    for key, value in message.items():
                        value = value[0]
                        if value['lender'] in self.LB:
                            result_text += '{}的{}到期的质押{}借贷{}订单的实时LTV为{}%\n'.format(
                                value['borrower'],
                                value['end_date'],
                                value['collateral'],
                                value['borrow'],
                                round(float(value['ltv']) * 100, 2)
                            )

                except:
                    await self.ding_bot.send_alert("you meet problem : {}".format(message["message"]))
                await self.ding_bot.send(result_text)



        await asyncio.sleep(300)
        asyncio.ensure_future(self.info_push())

    def run(self):
        asyncio.ensure_future(self.info_push())
        asyncio.get_event_loop().run_forever()


if __name__ == "__main__":
    json_info = json.load(open("../ding.json"))
    mode = 'test'
    id_tuple=tuple(get_all_accrual(mode=mode))#保证获取到订单列表的环境和推送的是一致的
    if mode == 'production':
        api = json_info['cam_api']['api']
        secret = json_info['cam_api']['secret']
        url = json_info['cam_base_url']['business_url']
        ddingding_bot_info = json_info['order_info']
    elif mode == 'test':
        api = json_info['test_cam_api']['api']
        secret = json_info['test_cam_api']['secret']
        url = json_info['cam_base_url']['test_url']
        dingding_bot_info = json_info['test_bot']
    else:
        raise Exception('please check you mode')
    dingding = DingReporter(dingding_bot_info)

    bot = order_info_push(dingding, api_key=api, secret_key=secret, base_url=url, info_list=id_tuple,LB=["",""])
    #根据borrower和lender的名字来判断是借出还是借入，当borrower在LB当就是借入订单
    bot.run()
