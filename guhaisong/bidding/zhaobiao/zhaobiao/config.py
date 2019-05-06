# coding=utf-8

# redis配置
redis_pass = 'P@ssw0rd'
redis_nodes = [{'host': '10.122.44.109', 'port': 7000},
               {'host': '10.122.44.109', 'port': 7001},
               {'host': '10.122.44.109', 'port': 7002},
               {'host': '10.122.44.11', 'port': 7003},
               {'host': '10.122.44.11', 'port': 7004},
               {'host': '10.122.44.11', 'port': 7005},
               ]

# mongodb配置
# mongo_host = '10.122.30.10'
# mongo_port = 27017
mongo_nodes = 'mongodb://cbi:cbi.123qaz@10.122.44.110:20000,10.122.44.111:20000,10.122.44.112:20000'
# mongo_user = 'cbi'
# mongo_pass = 'cbi.123qaz'
mongo_db = 'gov_zb'

# [翻页深度,协程数,列表队列,集合]
# 重庆招标网
cqzb_list = [5, 15, 'cqzb_list_url', 'chongqing_cqzb_gov_cn']
# 贵州省招标投标公共服务平台
gzzbw_list = [5, 20, 'gzzbw_list_url', 'guizhou_gzzbw_cn']
# 中共中央直属机关采购中心
ccgp_list = [2, 20, 'ccgp_list_url', 'quanguo_zzcg_ccgp_gov_cn']
# 大连公共资源交易网
ggzyjy_list = [2, 10, 'ggzyjy_list_url', 'dalian_ggzyjy_dl_gov_cn']
# 5 河北省公共资源交易中心
hebpr_list = [2, 10, 'hebpr_list_url', 'hebei_hebpr_cn']
# 6石家庄市公共资源交易中心
sjzsxzspj_list = [2, 20, 'sjzsxzspj_list_url', 'shijiazhuang_sjzsxzspj_gov_cn']
# 7 深圳公共资源交易平台
szggzy_list = [5, 20, 'szggzy_list_url', 'shenzhen_ggzy_sz_gov_cn']
# 8 广州公共资源交易中心
gzggzy_list = [5, 20, 'gzggzy_list_url', 'guangzhou_gzggzy_cn']
# 9 湖北公共资源交易中心
hbggzy_list = [5, 10, 'hbggzy_list_url', 'hubei_hbggzy_cn']
# 10 河南公共资源交易中心
hnggzy_list = [5, 10, 'hnggzy_list_url', 'henan_hnggzy_com']
# 11 长沙公共资源交易监管网
csggzy_list = [5, 20, 'csggzy_list_url', 'changsha_csggzy_gov_cn']
# 12 吉林省政府采购中心
jlszfcg_list = [5, 20, 'jlszfcg_list_url', 'jilin_jlszfcg_gov_cn']
# 13 长春政府采购中心
ccgp_com_list = [5, 20, 'ccgp_list_url', 'chuangchun_ccgp_com_cn']
# 14 北京政府采购中心
bgpc_gov_list = [5, 5, 'bgpc_gov_list_url', 'beijing_bgpc_gov_cn']
# 15 广西壮族自治区政府采购
gxgp_list = [5, 20, 'gxgp_list_url', 'guangxi_gxgp_gov_cn']
# 16 内蒙古政府采购中心
nmgzfcg_list = [5, 20, 'nmgzfcg_list_url', 'neimeng_nmgzfcg_gov_cn']
# 17 南宁市政府集中采购中心
purchase_list = [5, 20, 'purchase_list_url', 'nanling_purchase_gov_cn']
# 18 太原市政府采购
tyzfcg_list = [5, 00, 'tyzfcg_list_url', 'taiyuan_tyzfcg_gov_cn']
# 19 湖北政府采购中心
hubeigp_list = [5, 20, 'hubeigp_list_url', 'hubei_hubeigp_gov_cn']
# 20 海南省公共资源交易平台
hainan_list = [5, 20, 'hainan_list_url', 'hainan_gov_cn']
# 21 全国招标信息网
zbtb_list = [5, 20, 'zbtb_list_url', 'quanguo_zbtb_com_cn']
# 22 黑龙江政府采购
hljzfcg_list = [5, 10, 'hljzfcg_list_url', 'heilongjiang_hljzfcg_xwzs']
# 23 国家税务总局
chinatax_list = [5, 1, 'chinatax_list_url', 'quanguo_chinatax_gov_cn']
# 24 中国海关政府采购
hgcg_list = [5, 4, 'hgcg_list_url', 'quanguo_hgcg_customs_gov_cn']

