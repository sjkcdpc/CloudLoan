# -*- coding: UTF-8 -*-
"""
@auth:bxj
@date: 2019-08-13
@describe:金服侠-牙医贷一期流程用例
"""

import unittest
import os
import json
import time
import sys

from common.common_func import Common
from log.logger import Logger
from common.open_excel import excel_table_byname
from config.configer import Config
from common.get_sql_data import GetSqlData

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

logger = Logger(logger="test_jfx_tp").getlog()


class JfxTp(unittest.TestCase):

	@classmethod
	def setUpClass(cls):
		cls.cm = Common()
		cls.env = sys.argv[3]
		cls.sql = GetSqlData()
		cls.r = cls.cm.conn_redis(enviroment=cls.env)
		file = Config().get_item('File', 'jfx_case_file')
		cls.excel = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + file

	@classmethod
	def tearDownClass(cls):
		pass

	def test_100_credit_apply(self):
		"""额度授信"""
		data = excel_table_byname(self.excel, 'credit_apply_data')
		print("接口名称:%s" % data[0]['casename'])
		self.cm.p2p_get_userinfo('jfx', self.env)
		self.r.mset(
			{
				"jfx_sourceUserId": self.cm.get_random('userid'),
				'jfx_transactionId': self.cm.get_random('transactionId'),
				"jfx_phone": self.cm.get_random('phone'),
				"jfx_firstCreditDate": self.cm.get_time()
			}
		)
		param = json.loads(data[0]['param'])
		param['personalInfo'].update(
			{
				"cardNum": self.r.get('jfx_cardNum'),
				"custName": self.r.get('jfx_custName'),
				"isDoctor": 0,
				"applicantClinicRelationship": 1
			}
		)
		param['applyInfo'].update({"applyTime": self.cm.get_time()})
		param.update(
			{
				"sourceUserId": self.r.get('jfx_sourceUserId'),
				"serviceSn": self.cm.get_random('serviceSn'),
				"transactionId": self.r.get('jfx_transactionId')
			}
		)
		param["entityInfo"]["enterpriseCertificateNum"] = Common.get_random("transactionId")
		param["entityInfo"]["enterpriseCertificateType"] = 1
		# del param["imageInfo"]["businessLicense"]
		# del param["imageInfo"]["medicalPracticeCertificate"]
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		headers["X-TBC-SKIP-SIGN"] = "true"
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		creditId = json.loads(rep.text)['content']['creditId']
		userId = json.loads(rep.text)['content']['userId']
		self.r.mset(
			{
				"jfx_creditId": creditId,
				"jfx_userId": userId
			}
		)
		self.assertEqual(json.loads(rep.text)['resultCode'], int(data[0]['resultCode']))

	def test_101_sign_credit(self):
		"""上传授信协议"""
		data = excel_table_byname(self.excel, 'contract_sign')
		print("接口名称:%s" % data[0]['casename'])
		param = self.cm.get_json_data('data', 'jfx_credit_contract_sign.json')
		param.update(
			{
				"serviceSn": self.cm.get_random('serviceSn'),
				"sourceUserId": self.r.get('jfx_sourceUserId'),
				"contractType": 1,
				"sourceContractId": self.cm.get_random('userid'),
				"transactionId": self.r.get('jfx_transactionId'),
				"associationId": self.r.get('jfx_creditId')
			}
		)
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(int(data[0]['resultCode']), json.loads(rep.text)['resultCode'])

	def test_102_query_result(self):
		"""授信结果查询"""
		self.sql.credit_set(
			enviroment=self.env,
			credit_id=self.r.get("jfx_creditId")
		)
		data = excel_table_byname(self.excel, 'credit_query_result')
		print("接口名称:%s" % data[0]['casename'])
		param = json.loads(data[0]['param'])
		param.update({"creditId": self.r.get('jfx_creditId')})
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(json.loads(rep.text)['resultCode'], int(data[0]['resultCode']))

	def test_103_query_user_amount(self):
		"""用户额度查询"""
		data = excel_table_byname(self.excel, 'query_user_amount')
		print("接口名称:%s" % data[0]['casename'])
		param = json.loads(data[0]['param'])
		param.update(
			{
				"sourceUserId": self.r.get('jfx_sourceUserId'),
				"userId": self.r.get('jfx_userId')
			}
		)
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(json.loads(rep.text)['resultCode'], int(data[0]['resultCode']))

	def test_104_project_apply(self):
		"""进件"""
		data = excel_table_byname(self.excel, 'test_project')
		print("接口名称:%s" % data[0]['casename'])
		param = json.loads(data[0]['param'])
		self.r.set('jfx_sourceProjectId', self.cm.get_random('sourceProjectId'))
		param.update(
			{
				"sourceProjectId": self.r.get('jfx_sourceProjectId'),
				"sourceUserId": self.r.get('jfx_sourceUserId'),
				"transactionId": self.r.get('jfx_transactionId')
			}
		)
		param['personalInfo'].update(
			{
				"cardNum": self.r.get('jfx_cardNum'),
				"custName": self.r.get('jfx_custName'),
				"phone": self.r.get('jfx_phone')
			}
		)
		param['applyInfo'].update({"applyTime": self.cm.get_time()})
		param['cardInfo'].update(
			{
				"bankNameSub": "建设银行",
				"bankCode": 34,
				"bankCardNo": "6227002432220410613",  # 6227002432220410613
				"unifiedSocialCreditCode": self.cm.get_random("businessLicenseNo")
			}
		)
		self.r.set("jfx_corporateAccountName", param['cardInfo']['corporateAccountName'])
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		projectId = json.loads(rep.text)['content']['projectId']
		self.r.set('jfx_projectId', projectId)
		self.assertEqual(json.loads(rep.text)['resultCode'], int(data[0]['resultCode']))

	def test_105_query_apply_result(self):
		"""进件结果查询"""
		GetSqlData.change_project_audit_status(
			project_id=self.r.get('jfx_projectId'),
			enviroment=self.env
		)
		data = excel_table_byname(self.excel, 'project_query_apply_result')
		print("接口名称:%s" % data[0]['casename'])
		param = json.loads(data[0]['param'])
		param.update(
			{
				"sourceProjectId": self.r.get('jfx_sourceProjectId'),
				"projectId": self.r.get('jfx_projectId')
			}
		)
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(int(data[0]['resultCode']), json.loads(rep.text)['resultCode'])

	def test_106_sign_credit(self):
		"""上传授信协议"""
		data = excel_table_byname(self.excel, 'contract_sign')
		print("接口名称:%s" % data[0]['casename'])
		param = self.cm.get_json_data('data', 'jfx_credit_contract_sign.json')
		param.update(
			{
				"serviceSn": self.cm.get_random('serviceSn'),
				"sourceUserId": self.r.get('jfx_sourceUserId'),
				"contractType": 5,
				"sourceContractId": self.cm.get_random('userid'),
				"transactionId": self.r.get('jfx_transactionId'),
				"associationId": self.r.get('jfx_projectId')
			}
		)
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(int(data[0]['resultCode']), json.loads(rep.text)['resultCode'])

	def test_107_contract_sign(self):
		"""上传借款合同"""
		data = excel_table_byname(self.excel, 'contract_sign')
		print("接口名称:%s" % data[0]['casename'])
		param = self.cm.get_json_data('data', 'jfx_borrow_period_contract_sign.json')
		param.update(
			{
				"serviceSn": self.cm.get_random('serviceSn'),
				"sourceUserId": self.r.get('jfx_sourceUserId'),
				"contractType": 2,
				"sourceContractId": self.cm.get_random('userid'),
				"transactionId": self.r.get('jfx_transactionId'),
				"associationId": self.r.get('jfx_projectId')
			}
		)
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(int(data[0]['resultCode']), json.loads(rep.text)['resultCode'])

	def test_108_pfa(self):
		"""放款"""
		data = excel_table_byname(self.excel, 'project_loan')
		param = json.loads(data[0]['param'])
		param.update(
			{
				"sourceProjectId": self.r.get('jfx_sourceProjectId'),
				"projectId": self.r.get('jfx_projectId'),
				"sourceUserId": self.r.get('jfx_sourceUserId'),
				"serviceSn": self.cm.get_random('serviceSn'),
				"accountName": self.r.get("jfx_corporateAccountName"),
				"bankCode": 34,
				"accountNo": "6227002432220410613"  # 6227002432220410613
			}
		)
		self.r.set("jfx_pfa_serviceSn", param['serviceSn'])
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(int(data[0]['resultCode']), json.loads(rep.text)['resultCode'])
		time.sleep(8)
		self.sql.change_pay_status(
			enviroment=self.env,
			project_id=self.r.get('jfx_projectId')
		)
		self.sql.loan_set(enviroment=self.env, project_id=self.r.get('jfx_projectId'))

	def test_109_pfa_query(self):
		"""放款结果查询"""
		data = excel_table_byname(self.excel, 'pfa_query')
		param = json.loads(data[0]['param'])
		param.update({"serviceSn": self.r.get('jfx_pfa_serviceSn')})
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			enviroment=self.env,
			product="cloudloan"
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(json.loads(rep.text)['resultCode'], int(data[0]['resultCode']))

	def test_110_query_repaymentplan(self):
		"""还款计划查询"""
		data = excel_table_byname(self.excel, 'repayment_plan')
		param = json.loads(data[0]['param'])
		param.update({"projectId": self.r.get('jfx_projectId')})
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product="cloudloan",
			enviroment=self.env
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(int(data[0]['resultCode']), json.loads(rep.text)['resultCode'])
		self.r.set("jfx_repayment_plan", json.dumps(json.loads(rep.text)['content']['repaymentPlanList']))

	@unittest.skipUnless(sys.argv[4] == "repayment", "条件成立时执行")
	# @unittest.skip("11")
	def test_112_repayment(self):
		"""还款流水推送"""
		data = excel_table_byname(self.excel, 'repayment')
		param = json.loads(data[0]['param'])
		repayment_plan_list = self.r.get("jfx_repayment_plan")
		success_amount = 0.00
		repayment_detail_list = []
		period = 1
		for i in json.loads(repayment_plan_list):
			if i['period'] == period:
				plan_detail = {
					"sourceRepaymentDetailId": Common.get_random("transactionId"),
					"payAmount": i['restAmount'],
					"planCategory": i['repaymentPlanType']
				}
				success_amount = round(success_amount + plan_detail.get("payAmount"), 2)
				repayment_detail_list.append(plan_detail)
		param.update(
			{
				"sourceRequestId": Common.get_random("requestNum"),
				"projectId": self.r.get("jfx_projectId"),
				"sourceProjectId": self.r.get("jfx_sourceProjectId"),
				"sourceUserId": self.r.get("jfx_sourceUserId"),
				"serviceSn": Common.get_random("serviceSn"),
				"payTime": Common.get_time("-"),
				"successAmount": success_amount,
				"period": period
			}
		)
		param['repaymentDetailList'] = repayment_detail_list
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			enviroment=self.env,
			product="cloudloan"
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(json.loads(rep.text)['resultCode'], int(data[0]['resultCode']))

	@unittest.skipUnless(sys.argv[4] == "repayment", "条件成立时执行")
	# @unittest.skip("11")
	def test_113_capital_flow(self):
		"""资金流水推送"""
		data = excel_table_byname(self.excel, 'cash_push')
		param = json.loads(data[0]['param'])
		success_amount = GetSqlData.get_repayment_amount(
			project_id=self.r.get("jfx_projectId"),
			enviroment=self.env,
			period=1
		)
		param.update(
			{
				"serviceSn": Common.get_random("serviceSn"),
				"projectId": self.r.get("jfx_projectId"),
				"sourceProjectId": self.r.get("jfx_sourceProjectId"),
				"repaymentPlanId": None,
				# "repaymentPlanId": Common.get_random("sourceProjectId"),
				"sucessAmount": success_amount,
				"sourceRepaymentId": Common.get_random("sourceProjectId"),
				"tradeTime": Common.get_time(),
				"finishTime": Common.get_time()
			}
		)
		if len(data[0]['headers']) == 0:
			headers = None
		else:
			headers = json.loads(data[0]['headers'])
		rep = self.cm.response(
			faceaddr=data[0]['url'],
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			enviroment=self.env,
			product="cloudloan"
		)
		print("响应信息:%s" % rep)
		print("返回json:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(json.loads(rep.text)['resultCode'], int(data[0]['resultCode']))


if __name__ == '__main__':
	unittest.main()