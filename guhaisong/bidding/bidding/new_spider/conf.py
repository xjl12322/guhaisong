
# 设置mongodb数据库链接地址
MONGODB_CON = 'mongodb://10.122.33.93:27017/gov_zb'
MONGODB_DB = 'gov_zb'

# 代理地址
proxy_api = 'http://10.122.44.109:8082/get'

# 设置保存数据库的基本字段
save_temp_info = {'_id':'','title':'','status':'','area_name':'','source':'','publish_date':'','detail_url':'','content_html':'','create_time':'','zh_name':'','en_name':'',}

# 以下为爬虫配置项
gov_001 = {
	'zh_name':'中国政府采购网',
	'en_name':'China Government Procurement',
	'source':'http://www.ccgp.gov.cn/',
	'db_name':'china_ccgp_gov_cn',
}

gov_033 = {
	'zh_name':'甘肃政府采购网',
	'en_name':'Gansu Government Procurement',
	'source':'http://www.gszfcg.gansu.gov.cn/',
	'db_name':'gansu_gszfcg_gansu_gov_cn',
}

gov_071 = {
	'zh_name':'湖南省公共资源交易中心',
	'en_name':'Hunan Province Public resource',
	'source':'http://www.hnsggzy.com',
	'db_name':'hunan_hncg_gov_cn',
}

gov_080 = {
	'zh_name':'河北公共资源交易中心',
	'en_name':'Hebei Province Public resource',
	'source':'http://www.hebpr.gov.cn',
	'db_name':'hebei_hebpr_cn',
}
