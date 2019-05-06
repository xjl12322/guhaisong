# coding=utf-8

usable_user = 'good_tyc_user'  # 禁止修改
unusable_user = 'bad_tyc_user'  # 禁止修改
# 链接配置
login_api = 'https://www.tianyancha.com/cd/login.json'  # 禁止修改
search_api = 'https://www.tianyancha.com/search?key={}'  # 禁止修改
detail_api = 'https://www.tianyancha.com/company/{}'  # 禁止修改
branch_api = 'https://www.tianyancha.com/pagination/branch.xhtml?ps=20&pn={}&id={}'  # 禁止修改
stockholder_api = 'https://www.tianyancha.com/pagination/holder.xhtml?ps=20&pn={}&id={}'  # 禁止修改
investment_api = 'https://www.tianyancha.com/pagination/invest.xhtml?ps=20&pn={}&id={}'  # 禁止修改
annualreport_api = 'https://www.tianyancha.com/reportContent/{}/{}'  # 禁止修改
font_api = 'https://static.tianyancha.com/fonts-styles/fonts/{}/{}/tyc-num.svg'  # 禁止修改

# mongodb配置
mongo_nodes = 'mongodb://cbi:cbi.123qaz@10.122.44.110:20000,10.122.44.111:20000,10.122.44.112:20000'
# mongo_nodes = 'mongodb://127.0.0.1:27017'

# 天眼查搜索
mongo_db = 'tyc_search_log'
mongo_list_collection = 'tyc_list_log'
mongo_detail_collection = 'tyc_detail_log'
mongo_branch_collection = 'tyc_branch_log'
mongo_stockholder_collection = 'tyc_stockholder_log'
mongo_investment_collection = 'tyc_investment_log'
mongo_annualreport_collection = 'tyc_annualreport_log'

# 代码中心搜索
mongo_code_search_collection = 'code_search_log'

# 代理隧道配置
proxyMeta = "%(user)s:%(pass)s@%(host)s:%(port)s" % {
    "host": 'p5.t.16yun.cn',
    "port": '6445',
    "user": '16EKILSS',
    "pass": '527342',
}

# 天眼查cookies池配置
cookie_pool = 'tyc_cookie_pool'  # 禁止修改
cookie_reserves = 1


# 天眼查详情页更新
mongo_update_host = 'mongodb://10.122.33.99:27017'
tyc_detail_update_days = 60
mongo_update_db = 'tyc_auto_info'
# update_branch_new = 'branch'
update_parent_new = 'parent'


# 代理池链接
get_token_api = 'http://10.122.33.93:8083/get_token'
add_black_api = 'http://10.122.33.93:8083/add_black'



