# 工商信息接口说明

#### 项目介绍
如有侵权,邮件联系

#### 软件架构
1. 运行环境python3
2. 采用flask作为程序api框架
3. 采用redis作为数据交互节点(需要安装redis,并修改redis相关信息)

#### 第三方模块

1. requests ---> pip3 install requests
2. pyyaml ---> pip3 install pyyaml
3. redis ---> pip3 install redis
4. flask ---> pip3 install flask
5. flask_cors ---> pip3 install flask_cors
6. flask_limiter ---> pip3 install flask_limiter
6. lxml ---> pip3 install lxml

#### 接口
1. http://0.0.0.0:8081/   说明文档接口
2. 全局搜索模式    http://0.0.0.0:8081/business?mode=list&kw=搜索关键字
3. 精准id搜索模式  http://0.0.0.0:8081/business?mode=detail&kw=搜索内部id
4. 分支机构搜索模式 http://0.0.0.0:8081/business?mode=branch&kw=搜索内部id
5. 股东信息搜索模式  http://0.0.0.0:8081/business?mode=stockholder&kw=搜索内部id
6. 对外投资搜索模式  http://0.0.0.0:8081/business?mode=investment&kw=搜索内部id
7. 年报信息搜索模式  http://0.0.0.0:8081/business?mode=annualreport&kw=搜索内部id
8. 百度百科校验模式  http://127.0.0.1:8081/baike?kw=关键字  百科搜索

#### 错误代码
1. 10200 正常请求
2. 10400 内部程序被锁,无法内部调用程序
3. 10404 账号异常,无账号可用
4. 10500 无法获取内部token
5. 10501 内部请求失败
6. 10502 缺少请求参数
7. 10503 内部登录失败
8. 10505 搜索模式异常

#### 部署说明
0. 修改配置:config中相关配置信息
1. 测试部署:nohup python3 ApiServer.py
2. 生产部署:详情参考flask+nginx+uwsgi环境部署

#### 使用说明

1. 接口调用频率30次每分钟(可设置)
2. 先全局搜索获取内部id然后调用精准搜索获取详情信息

#### 字段中英对照
##### ----------------------------------------列表页 接口----------------------------------------
company_name------------公司名称  
company_id-----------------公司id  
company_state-------------公司状态  
legal_person----------------法人代表  
registered_capital----------注册资本  
registered_time-------------注册时间  
contact_phone--------------联系电话  
contact_mail-----------------联系邮箱  
short_name------------------公司简称  
history_name----------------历史名称  
credit_code------------------信用代码  
sign_up_code---------------注册号码  
org_code---------------------机构代码  
site-----------------------------所属城市  
##### ----------------------------------------详情页 接口----------------------------------------
###### ----------基础信息----------
company_id------------------天眼查id  
crawl_url----------------------天眼查链接  
secret_key-------------------加密秘钥  
company_name-------------公司名称  
update_time------------------更新时间  
history_name----------------历史名称  
company_tags--------------公司标签  
telphone----------------------联系电话    
email--------------------------联系邮箱    
website-----------------------公司官网  
company_addrss-----------公司地址  
company_abstract---------公司简介
###### ----------工商信息----------
legal_person----------------法人代表  
legal_person_id------------法人链接  
registered_capital---------注册资本  
registered_date------------注册日期  
company_status-----------公司状态  
register_number-----------工商注册号  
organization_code---------组织机构代码  
social_credit_code---------统一信用代码  
company_type--------------公司类型  
corporation_tax-------------纳税人识别号  
industry----------------------行业  
business_term--------------营业期限  
approval_date--------------核准日期  
taxpayer_aptitude----------纳税资质  
employees_num------------人员规模  
paid_capital------------------实缴资本  
registration_authority------登记机关  
insured_num-----------------参保人数  
company_enname----------英文名称  
registered_address--------注册地址  
operation_scope------------经营范围  
###### ----------股东信息(大股东)----------
big_holder-----------------------大股东  
big_holder_id-------------------大股东链接  
big_holder_investment--------大股东出资  
big_holder_investment_rate--大股东出资比例  
big_holder_investment_date-大股东出资时间  
###### ----------税务评级----------
tax_level---------------------------税务评级  
###### ----------融资历史----------
financing_info---------------------融资历史  
--01num----------------------------序号  
--02date----------------------------时间  
--03rounds-------------------------轮次  
--04appraisement----------------估值  
--05sum_of_money--------------金额  
--06rate----------------------------比例  
--07investor-----------------------资方  
##### ----------------------------------------分支机构 接口----------------------------------------
branch_company_id-------------子公司id  
branch_company_name--------子公司名称  
branch_legal_person------------法人或者负责人  
branch_reg_date-----------------注册日期  
branch_status---------------------公司状态  
##### ----------------------------------------股东信息 接口----------------------------------------
holder_name-----------------------股东名称  
holder_id----------------------------股东id  
investment_proportion-----------出资比例  
investment_amount--------------认缴出资  
investment_date------------------出资时间  
##### ----------------------------------------对外投资 接口----------------------------------------
invested_company_name ------被投资公司名称  
invested_company_id ----------被投资公司id  
legal_person----------------------被投资法定代表人  
registered_capital----------------注册资本  
investment_proportion-----------投资占比  
registered_date-------------------注册时间  
status-------------------------------状态  
##### ----------------------------------------年报信息 接口----------------------------------------
title-----------------------------------年报标题  
reg_code----------------------------注册号  
social_credit_code----------------信用代码  
company_name--------------------企业名称  
phone--------------------------------联系电话  
postalcode--------------------------邮政编码  
status--------------------------------经营状态  
employee_nums-------------------从业人数  
email---------------------------------电子邮箱  
website------------------------------是否有网店或者网站  
address-----------------------------公司地址  
total_assets------------------------资产总额  
total_equity-------------------------所有者权益合计  
total_salesquity--------------------销售总额  
total_profit--------------------------利润总额  
main_income-----------------------营业总收入中主营业务收入  
net_profit----------------------------净利润  
total_tax-----------------------------纳税总额  
total_liabilities----------------------负债总额  
endowment_insurance-----------城镇职工基本养老保险  
medical_insurance----------------职工基本医疗保险  
maternity_insurance--------------生育保险  
unemployed_insurance----------失业保险  
injury_insurance-------------------工伤保险


#### 参与贡献

1. chinapython

#### 联系方式
chinapython@yeah.net