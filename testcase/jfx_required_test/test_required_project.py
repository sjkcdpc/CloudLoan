# -*- coding: UTF-8 -*-
"""
@auth:bxj
@date:2019-08-23 09:28
@describe:牙医贷进件接口字段必填项校验
"""
import unittest
import os
import json
import ddt
import sys
from common.common_func import Common
from log.logger import Logger
from common.open_excel import excel_table_byname
from config.configer import Config

logger = Logger(logger="project").getlog()


@ddt.ddt
class JfxPorject(unittest.TestCase):
	file = Config().get_item('File', 'jfx_required_case_file')
	excel = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) + file
	excel_data = excel_table_byname(excel, 'project_null')

	@classmethod
	def setUpClass(cls):
		cls.env = 'qa'
		cls.url = JfxPorject.excel_data[0]['url']
		cls.headers = JfxPorject.excel_data[0]['headers']
		cls.param = JfxPorject.excel_data[0]['param']

	def tearDown(self):
		pass

	@ddt.data(*excel_data)
	def test_project(self, data):
		global key, value
		print("接口名称:%s" % data['casename'])
		case = data['casename']
		param = json.loads(self.param)
		key = str(case).split("空")[1].split(".")[0]
		value = str(case).split("空")[1].split(".")[1]
		param[key][value] = None
		headers = json.loads(self.headers)
		rep = Common.response(
			faceaddr=self.url,
			headers=headers,
			data=json.dumps(param, ensure_ascii=False).encode('utf-8'),
			product='cloudloan',
			enviroment=self.env
		)
		print("响应结果:%s" % rep)
		print("返回信息:%s" % rep.text)
		logger.info("返回信息:%s" % rep.text)
		self.assertEqual(json.loads(rep.text)['resultCode'], int(data['resultCode']))


if __name__ == '__main__':
	unittest.main()