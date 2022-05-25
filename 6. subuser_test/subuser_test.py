# -*- coding: utf-8 -*-
"""
 Created on：2022.3.3
 @author  : ivy
 @File    : subuser_test
 @Description: 子母账户功能测试
"""
import logging
import time
import asyncio
from rest_utils import api_key_get_hb, api_key_post_hb, http_get_request_hb  # request是可以把动作输入进去：get。pull'


class ProWorker:

    def __init__(self, api_key, secret_key, url=None):
        self.logger = logging.getLogger(self.__class__.__name__)
        if not url:
            self._url = 'https://api.huobi.pro'  # 现货
        else:
            self._url = url
        self._futures_url = 'https://api.hbdm.com'  # 期货，不同合约 是否是同一个入口？
        self.api_key = api_key
        self.secret_key = secret_key
        self.accid = self._get_account_id()
        self.logger.info('initialize pro worker, url: {}, api_key: {}, '
                         'secret_key: {}, accid: {}'.format(
            self._url, self.api_key, self.secret_key, self.accid))

    def _get_account_id(self):
        accid = None
        res = api_key_get_hb(
            self._url, '/v1/account/accounts', {}, self.api_key, self.secret_key)
        if res.get('status') == 'ok':
            for info in res.get('data'):
                if info["type"] == "spot":
                    accid = str(info["id"])
                    break
        if accid is None:
            raise Exception('fail to get account id')
        return accid

    # 母子账户之间的转账 TODO
    def subuser_transfer(self, sub_uid, currency, amount, transfer_type):
        res = api_key_post_hb(
            self._url, '/v1/subuser/transfer',
            {
                "sub-uid": sub_uid,
                "currency": currency,
                "amount": amount,
                "type": transfer_type
            },
            self.api_key, self.secret_key
        )
        if res.get('status') != 'ok':
            self.logger.error(res)
            print('ERROR!', res)
        return res.get('data')

    def transfer_parent_to_sub(self, sub_uid, currency, amount):
        return self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-out')

    def transfer_sub_to_parent(self, sub_uid, currency, amount):
        return self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-in')

    # new
    # 下单函数 TODO
    def place_order(self, acc_id, amount):
        res = api_key_post_hb(
            self._url, '/v1/order/orders/place',
            {
                "account-id": acc_id,
                "amount": amount,
                "symbol": "ethusdt",
                "type": "buy-limit",
            },
            self.api_key, self.secret_key
        )
        if res.get('status') != 'ok':
            self.logger.error(res)
            print('下单 ERROR!', res)
        return res.get('data')  # .get('deductMode')

    def create_subuser(self):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/creation',
            {
                "userList": [
                    {
                        "userName": "testsubuser0001",
                        "note": "test-subuser"
                    },
                ]
            },
            self.api_key, self.secret_key
        )
        if res.get('code') != 200:
            self.logger.error(res)
        return res.get('data').get('uid')  # .get('deductMode')

    def get_all_sub_uid(self):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/user-list',
            {},
            self.api_key, self.secret_key
        )
        if res.get('code') != 200:
            self.logger.error(res)
        # print(res.get('data'))
        uid_list = [i['uid'] for i in res.get('data')]
        return uid_list

    # 1. 设置子用户手续费抵扣模式
    def set_subuser_deduct_mode(self, sub_uid=380841561):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/deduct-mode',
            {
                "subUids": sub_uid,
                "deductMode": 'sub'
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        return res.get('data')  # .get('deductMode')

    # 2.冻结/解冻子账户
    def lock_unlock_subuser(self, sub_uid=380841561, action='lock'):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/management',
            {
                "subUid": sub_uid,
                "action": action
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        # print(res.get('data'))
        # 看查询功能是否正常
        sub_state = self.get_subuser_state(sub_uid)

        # 看下单功能是否正常 TODO
        sub_acc_id = self.get_subuser_acc_id(sub_uid)
        order = self.place_order(sub_acc_id, amount=0.0001)
        return '子账户状态：{}，下单状态：{}'.format(sub_state, order)

    def get_subuser_acc_id(self, sub_uid=380841561):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/account-list',
            {
                "subUid": sub_uid,
            },
            self.api_key, self.secret_key
        )
        if res.get('code') != 200:
            self.logger.error(res)
        # print(res.get('data'))
        return res.get('data').get('list')[2].get('accountIds')[0].get('accountId')

    # 3. 查询子账户用户状态
    def get_subuser_state(self, sub_uid=380841561):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/user-state',
            {
                "subUid": sub_uid,
            },
            self.api_key, self.secret_key
        )
        if res.get('code') != 200:  # 状态码 显示 api 获取异常
            self.logger.error(res)
        return res.get('data').get('userState')

    # 4. 设置子账户交易权限
    def set_subuser_trade(self, sub_uid=380841561):
        # 设置关闭 isolated margin 的交易权限
        is_res = api_key_post_hb(
            self._url, '/v2/sub-user/tradable-market',
            {
                "subUids": sub_uid,
                "accountType": 'isolated-margin',  # cross-margin
                "activation": 'deactivated'
            },
            self.api_key, self.secret_key
        )
        if not is_res.get('ok'):
            self.logger.error(is_res)
            print('ERROR!', is_res)
        # 尝试进行下单动作来确认状态 TODO
        sub_acc_id = self.get_subuser_acc_id(sub_uid)
        order = self.place_order(sub_acc_id, amount=0.0001)
        if order:
            print('!!仍可交易！！')

        # 设置关闭 cross margin 的交易权限
        cr_res = api_key_post_hb(
            self._url, '/v2/sub-user/tradable-market',
            {
                "subUids": sub_uid,
                "accountType": 'cross-margin',  # cross-margin
                "activation": 'deactivated'
            },
            self.api_key, self.secret_key
        )
        if not cr_res.get('ok'):
            self.logger.error(cr_res)
            print('ERROR!', cr_res)
        # 尝试进行下单动作来确认状态 TODO
        sub_acc_id = self.get_subuser_acc_id(sub_uid)
        order = self.place_order(sub_acc_id, amount=0.0001)
        if order:
            print('!!仍可交易！！')
        return is_res.get('data')[0].get('activation'), cr_res.get('data')[0].get('activation')  #

    def get_access_key(self, uid):
        res = api_key_get_hb(
            self._url, '/v2/user/api-key',
            {
                "uid": uid,
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        # print(res.get('data'))
        return res.get('data')[0].get('accessKey')

    # 5. 修改子账户 API key
    def modify_subuser_api_key(self, sub_uid, sub_accessKey):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/api-key-modification',
            {
                "subUid": sub_uid,
                "accessKey": sub_accessKey,  # cross-margin
                "permission": 'readOnly'
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)
        # print(res.get('data'))

        # 测试账户是否能够进行交易 TODO
        sub_acc_id = self.get_subuser_acc_id(sub_uid)
        order = self.place_order(sub_acc_id, amount=0.0001)

        # 测试在不传入 ipAddress 这个参数的情况下是否会将原有设置的 ip 地址给删除掉
        if not res.get('data').get('ipAddresses'):
            ip_test = '不传入 ipAddress 参数会将原有设置的 ip 地址给删除掉'
        return '交易测试结果：{}, ip配置测试：{}'.format(order, ip_test)

    # 子账户之间的转账 TODO
    def transfer_sub_to_sub(self, sub_uid_from, sub_uid_to, currency, amount):
        acc_id_from = self.get_subuser_acc_id(sub_uid=sub_uid_from)
        acc_id_to = self.get_subuser_acc_id(sub_uid=sub_uid_to)
        res = api_key_post_hb(
            self._url, '/v1/account/transfer',
            {
                "from-user": sub_uid_from,
                "from-account-type": 'spot',
                "from-account": acc_id_from,
                "to-user": sub_uid_to,
                "to-account-type": 'spot',
                "to-account": acc_id_to,
                "currency": currency,
                "amount": amount
            },
            self.api_key, self.secret_key
        )
        if res.get('status') != 'ok':
            self.logger.error(res)
            print('ERROR!', res)
        return res.get('data')

    # 6. 设置子账户资产转出权限
    def set_subuser_transferable(self, sub_uid1, sub_uid2):
        res = api_key_post_hb(
            self._url, '/v2/sub-user/transferability',
            {
                "subUids": sub_uid1,
                "accountType": 'spot',  # cross-margin
                "transferrable": 'false'
            },
            self.api_key, self.secret_key
        )
        if not res.get('ok'):
            self.logger.error(res)
            print('ERROR!', res)

        # 进行 子账户到母账户 的转账操作 TODO
        currency, amount = 'usdt', 0.0001
        sub2parent = self.transfer_sub_to_parent(sub_uid1, currency, amount)
        # 进行 子账户到子账户 的转账操作 TODO
        sub2sub = self.transfer_sub_to_sub(sub_uid1, sub_uid2, currency, amount)
        return sub2parent, sub2sub  # 转账结果

    # 7. 母子账户之间资产划转 TODO
    def check_4_sub_transfer(self, sub_uid, currency, amount):
        trans1 = self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-in')  # 子用户划转给母用户虚拟币
        trans2 = self.subuser_transfer(sub_uid, currency, amount, 'master-transfer-out')  # 母用户划转给子用户虚拟币
        trans3 = self.subuser_transfer(sub_uid, currency, amount, 'master-point-transfer-in')  # 子用户划转给母用户点卡
        trans4 = self.subuser_transfer(sub_uid, currency, amount, 'master-point-transfer-out')  # 母用户划转给子用户点卡
        return trans1, trans2, trans3, trans4

    def test_fist_7_func(self):
        # 获取子账户 uid
        sub_uid_list = self.get_all_sub_uid()
        while len(sub_uid_list) < 2:
            sub_uid_list.append(self.create_subuser())
        sub_uid1, sub_uid2 = sub_uid_list[0], sub_uid_list[1]
        # print(sub_uid1, sub_uid2)

        # 1. 设置子用户手续费抵扣模式
        re1 = self.set_subuser_deduct_mode(sub_uid1)
        print(f'test 1|设置子用户手续费抵扣模式| 子账户{re1[0].get("subUid")}的手续费抵扣模式: {re1[0].get("deductMode")}')

        # 2.冻结/解冻子账户
        re2_lock = self.lock_unlock_subuser(sub_uid1, action='lock')
        re2_unlock = self.lock_unlock_subuser(sub_uid1, action='unlock')
        print(f'test 2|冻结/解冻子账户| 冻结：{re2_lock}; 解冻：{re2_unlock}')

        # 3. 查询子账户用户状态
        sub_state = self.get_subuser_state(sub_uid1)
        print(f"test 3|查询子账户用户状态| 子账户{sub_uid1}的状态: {sub_state}")

        # 4. 设置子账户交易权限
        re4 = self.set_subuser_trade(sub_uid1)
        print(f"test 4|设置子账户交易权限| 关闭solated margin权限后是否可交易：{re4[0]}，关闭cross margin权限后是否可交易：{re4[1]}")

        # 5. 修改子账户 API key
        accesskey = self.get_access_key(sub_uid1)
        re5 = self.modify_subuser_api_key(sub_uid1, accesskey)
        print(f"test 5|修改子账户 API key| {re5}")

        # 6. 设置子账户资产转出权限
        sub2parent, sub2sub = self.set_subuser_transferable(sub_uid1, sub_uid2)
        print(f"test 6 |设置子账户资产转出权限| 设置权限关闭后，子账户转母账户 {sub2parent}，子账户转子账户 {sub2sub}")

        # 7. 母子账户之间资产划转
        t1, t2, t3, t4 = self.check_4_sub_transfer(sub_uid1, currency='usdt', amount=0.0001)
        print(f"test 7 |母子账户之间资产划转| 子用户划转给母用户虚拟币:{t1}, 母用户划转给子用户虚拟币:{t2},"
              f"子用户划转给母用户点卡:{t3}, 母用户划转给子用户点卡:{t4}")

    #8.子母账户获取用户UID
    def get_UID(self):
        uid = None
        res = api_key_get_hb(self._url, '/v2/user/uid', {}, self.api_key, self.secret_key)
        uid = res.get('data')
        if uid is None:
            raise Exception('fail to get account id')
        print('用户UID为：', uid)
        return uid

    #9.子账户充币地址查询 TODO
    def get_sub_deposit_address(self, self_uid, currency):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/deposit-address',
            {
                'subUid': self_uid,
                'currency': currency,
            },
            self.api_key, self.secret_key
        )
        print('子账户充币地址为：', res.get('data'))
        return res.get('data')

    #10.子用户充币记录查询 TODO
    def get_sub_deposit(self,self_uid,currency=None,starttime=None,endtime=None,sort=None,limit=None,fromld=None):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/query-deposit',
            {
                'subUid': self_uid,
                'currency': currency,  #省缺为所有币种
                'startTime':starttime,  #省缺为endtime-30天
                'endTime': endtime,     #省缺为当前时间
                'sort': sort,           #省缺为desc由近及远
                'limit':limit,          #单页最大返回条目数量 [1-500] （缺省值100）
                'fromId':fromld         #起始充币订单ID
            },
            self.api_key, self.secret_key
        )
        print('子用户充币记录：',res.get('data'))
        return res.get('data')

    #11.子用户余额汇总  TODO
    def get_sub_balance_summary(self):
        balance = None
        res = api_key_get_hb(self._url, '/v1/subuser/aggregate-balance', {}, self.api_key, self.secret_key)
        balance = res.get('data')
        if balance is None:
            raise Exception('fail to get account id')
        print('当前子账户余额汇总信息为：', balance)
        return balance

    #12.子用户余额   TODO
    def get_sub_balance(self, self_uid):
        res = api_key_get_hb(
            self._url, '/v1/account/accounts/{sub_uid}'.format(sub_uid=self_uid),
            {}, self.api_key, self.secret_key)
        if res.get('status') != 'ok':
            self.logger.error(res)
        print('子用户{}的余额信息为'.format(self_uid),res.get('data'))
        return res.get('data')
    #查找所有子账户
    def get_sub_uid(self):
        res = api_key_get_hb(
            self._url, '/v2/sub-user/user-list',
            {}, self.api_key, self.secret_key)
        if res.get('status') != 'ok':
            self.logger.error(res)

        return res.get('data')
    #创建子账户
    def create_sub(self):
        res = api_key_post_hb(self._url, '/v2/sub-user/creation',
            {
                "userList": [
                    {
                        "userName": "testsublin",
                        "note": "huobi"
                    }
                ]
            },
            self.api_key, self.secret_key)
        return res.get('data')

if __name__ == '__main__':
    api = '***'
    secret = '****'
    test = ProWorker(api_key=api, secret_key=secret)
    #1-7
    #q=test.test_fist_7_func()
    #8.获取UID
    #a = test.get_UID()
    #9.获取充币地址
    #b= test.get_sub_deposit_address(self_uid=****,currency='usdt')
    #10.获取充币记录
    #c=test.get_sub_deposit(self_uid=****)
    #11.获取子用户余额汇总
    #d=test.get_sub_balance_summary()
    #12.子用户余额查询
    #e=test.get_sub_balance(self_uid=*****)


