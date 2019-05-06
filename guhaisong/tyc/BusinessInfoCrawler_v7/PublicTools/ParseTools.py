# coding=utf-8
import re
import time
import hashlib
from lxml import etree
from copy import deepcopy
from FontCracks import Fonts


class ParseHelper:
    def __init__(self):
        self.Fonts = Fonts.Font()

    # MD5加密模块
    def md5(self, string):
        hl = hashlib.md5()
        hl.update(string.encode(encoding='utf-8'))
        return hl.hexdigest()[8:-8]

    # 天眼查列表信息
    def list_parse(self, response):
        item, items, html = {}, [], etree.HTML(response)
        selectors = html.xpath('//div[contains(@class,"search-result-single")]/div[contains(@class,"content")]')
        for selector in selectors:
            # 公司名称  company_name
            item['company_name'] = (
                ''.join(selector.xpath('./div[contains(@class,"header")]/a//text()'))).strip()
            # 公司链接 company_url
            company_url = (''.join(selector.xpath('./div[contains(@class,"header")]/a/@href'))).strip()
            # 公司id company_id
            item['company_id'] = str(company_url).split('/')[-1]
            # 公司状态 company_state
            item['company_state'] = (''.join(selector.xpath(
                './div[contains(@class,"header")]/div[contains(@class,"num-opening")]/text()'
            ))).strip()
            # 法人代表 legal_person
            legal_person_temp = (''.join(selector.xpath(
                './div[contains(@class,"info")]/div[contains(text(),"法定代表人") or contains(text(),"负责人")]/a/text()'
            ))).strip()
            item['legal_person'] = legal_person_temp if len(legal_person_temp) != 0 else (
                ''.join(selector.xpath(
                    './div[contains(@class,"info")]/div[contains(text(),"法定代表人")]/span/text()'
                ))).strip()
            # 注册资本  registered_capital
            item['registered_capital'] = (''.join(selector.xpath(
                './div[contains(@class,"info")]/div[contains(text(),"注册资本")]/span/text()'
            ))).strip()
            # 注册时间  registered_time
            item['registered_time'] = (''.join(selector.xpath(
                './div[contains(@class,"info")]/div[contains(text(),"成立日期")]/span/text()'
            ))).strip()
            # 联系电话  contact_phone
            contact_phone_temp = selector.xpath(
                './div[contains(@class,"contact")]//span[contains(text(),"联系电话")]/following-sibling::*//text()')
        
            if len(contact_phone_temp) == 1:
                item['contact_phone'] = [''.join(contact_phone_temp[0]).strip()]
            elif len(contact_phone_temp) == 3:
                item['contact_phone'] = eval(contact_phone_temp[0])
            else:
                item['contact_phone'] = []
            item['contact_phone'] = ','.join(item['contact_phone'])
            # 联系邮箱 contact_mail
            contact_mail_temp = selector.xpath(
                './div[contains(@class,"contact")]//span[contains(text(),"邮箱")]'
                '/following-sibling::*[text()!="查看更多"]/text()')
            if len(contact_mail_temp) == 1:
                item['contact_mail'] = [''.join(contact_mail_temp[0]).strip()]
            elif len(contact_mail_temp) == 2:
                item['contact_mail'] = eval(contact_mail_temp[1])
            else:
                item['contact_mail'] = []
            item['contact_mail'] = ','.join(item['contact_mail']).strip('...').strip()
            # 公司简称  short_name
            item['short_name'] = (''.join(selector.xpath(
                './div/span[contains(text(),"公司简称")]/following-sibling::span//text()'
            ))).strip()
            # 历史名称 history_name
            item['history_name'] = (''.join(selector.xpath(
                './div/span[contains(text(),"历史名称")]/following-sibling::span//text()'
            ))).strip()
            # 信用代码 credit_code
            item['credit_code'] = (''.join(selector.xpath(
                './div/span[contains(text(),"信用代码")]/following-sibling::span//text()'
            ))).strip()
            # 注册号码 sign_up_code
            item['sign_up_code'] = (''.join(selector.xpath(
                './div/span[contains(text(),"注册号码")]/following-sibling::span//text()'
            ))).strip()
            # 机构代码 org_code
            item['org_code'] = (''.join(selector.xpath(
                './div/span[contains(text(),"机构代码")]/following-sibling::span//text()'
            ))).strip()
            # 所属城市  site
            item['site'] = ''.join(selector.xpath('./following-sibling::span/text()'))
            items.append(deepcopy(item))
        return items

    # 天眼查详情页信息
    def detail_parse(self, keyword, response):
        item, html = {}, etree.HTML(response)
        # --------------------基础信息--------------------
        # 天眼查id  id
        item['company_id'] = keyword  # 关键字
        # 天眼查链接 url
        item['crawl_url'] = 'https://www.tianyancha.com/company/{}'.format(keyword)
        # 加密秘钥 secret_key
        item['secret_key'] = ''.join(
            html.xpath('//body[contains(@class,"font-")]/@class')).strip().replace('font-', '')
        mapping = self.Fonts.NumDecrypt(key=item['secret_key'])
        # 公司名称 company_name_zh
        item['company_name'] = ''.join(html.xpath(
            '//div[contains(@class,"content")]/div[contains(@class,"header")]/h1/text()')).strip()
        # 更新时间  update_time
        item['update_time'] = ''.join(html.xpath('//span[contains(@class,"updatetimeComBox")]/text()')).strip()
        # 历史名称 history_name
        item['history_name'] = ','.join(html.xpath(
            '//div[text()="曾用名"]/div[contains(@class,"history-content")]//text()'))
        # 公司标签  company_tags
        item['company_tags'] = ','.join(
            html.xpath('//div[@class="tag-list"]/span[contains(@class,"tag-new-category")]//text()'))
        # 联系电话  telphone
        telphone_temp = list(set(html.xpath('//span[text()="电话："]/following-sibling::span//text()')))
        temp = sorted([float(str(len(i)) + '.' + str(telphone_temp.index(i))) for i in telphone_temp])
        item['telphone'] = '' if len(temp) == 0 else str(telphone_temp[int(str(temp[-1]).split('.')[-1])]).replace(
            '[', '').replace(']', '').replace('"', '').replace("'", '')
        # 联系邮箱  email
        email_temp = html.xpath('//span[text()="邮箱："]/following-sibling::span//text()')
        # email = [] if len(email_temp) == 0 else email_temp if len(email_temp) == 1 else eval(email_temp[-1])
        # item['email'] = ','.join(email)
        temp = sorted([float(str(len(i)) + '.' + str(email_temp.index(i))) for i in email_temp])
        item['email'] = '' if len(temp) == 0 else str(email_temp[int(str(temp[-1]).split('.')[-1])]).replace(
            '[', '').replace(']', '').replace('"', '').replace("'", '')
        # 公司官网 website
        website_temp = ''.join(html.xpath('//span[text()="网址："]/following-sibling::a//@href')).strip()
        item['website'] = website_temp if len(website_temp) != 0 else '暂无信息'
       
        # 公司地址  company_addrss
        company_addrss_temp = html.xpath('//span[text()="地址："]/..//text()')
        if len(company_addrss_temp) != 0:
            item['company_addrss'] = str(company_addrss_temp[2]).strip() if '详情' in str(
                company_addrss_temp).strip() else str(company_addrss_temp[-2]).strip()
        else:
            item['company_addrss'] = '解析失败'
            
        # 公司简介  company_abstract
        company_abstract = html.xpath('//span[text()="简介："]/..//text()')
        if len(company_abstract) != 0:
            item['company_abstract'] = \
                str(company_abstract[-2]).strip() if '详情' in str(company_abstract) else str(
                    company_abstract[-1]).strip()
        else:
            item['company_abstract'] = '解析失败'
        # --------------------工商信息--------------------
        # 法人代表  legal_person
        item['legal_person'] = ''.join(
            html.xpath('//div[contains(@class,"humancompany")]/div[contains(@class,"name")]//text()')).strip()
        # 法人链接  legal_person_id
        item['legal_person_id'] = ''.join(html.xpath(
            '//div[contains(@class,"humancompany")]/div[contains(@class,"name")]/a/@href')).strip(
            'https://www.tianyancha.com/human/').strip()
        # 注册资本 registered_capital
        # item['registered_capital'] = ''.join(html.xpath('//div[contains(text(),"注册资本")]/following-sibling::div[1]/@title')).strip()
        item['registered_capital'] = ''.join(html.xpath('//div[@id="_container_baseInfo"]/table[2]/tbody/tr[1]/td[2]/div/@title')).strip()
        # 注册时间 registered_date
        # registered_date = ''.join(html.xpath('//div[contains(text(),"注册时间")]/following-sibling::div[1]/text/text()')).strip()
        item['registered_date'] = ''.join(html.xpath('//div[@id="_container_baseInfo"]/table[2]/tbody/tr[1]/td[4]/div//text()')).strip()
        # item['registered_date'] = '密文:' + registered_date if mapping is None else ''.join(
        #     [mapping[i] if i in mapping.keys() else i for i in registered_date])
        # 公司状态  company_status
        # item['company_status'] = ''.join(html.xpath('//div[@class="num-opening"]//text()')).strip()
        item['company_status'] = ''.join(html.xpath('//*[@id="_container_baseInfo"]/table[2]/tbody/tr[2]/td[2]/text()')).strip()
        # 工商注册号 register_number
        item['register_number'] = ''.join(html.xpath(
            '//td[text()="工商注册号"]/following-sibling::td[1]//text()')).strip()
        # 组织机构代码  organization_code
        item['organization_code'] = ''.join(
            html.xpath('//td[text()="组织机构代码"]/following-sibling::td[1]//text()')).strip()
        # 统一信用代码  social_credit_code
        item['social_credit_code'] = ''.join(
            html.xpath('//td[contains(text(),"信用代码")]/following-sibling::td[1]/text()')).strip()
        # 公司类型  company_type
        item['company_type'] = ''.join(
            html.xpath('//td[text()="公司类型"]/following-sibling::td[1]//text()')).strip()
        # 纳税人识别号 corporation_tax
        item['corporation_tax'] = ''.join(
            html.xpath('//td[text()="纳税人识别号"]/following-sibling::td[1]//text()')).strip()
        # 行业  industry
        item['industry'] = ''.join(
            html.xpath('//td[text()="行业"]/following-sibling::td[1]//text()')).strip()
        # 营业期限  business_term
        item['business_term'] = ''.join(
            html.xpath('//td[text()="营业期限"]/following-sibling::td[1]//text()')).strip()
        # 核准日期  approval_date
        approval_date = ''.join(
            html.xpath('//td[contains(text(),"核准日期")]/following-sibling::td[1]/text/text()')).strip()
        item['approval_date'] = '密文:' + approval_date if mapping is None else ''.join(
            [mapping[i] if i in mapping.keys() else i for i in approval_date])
        # 纳税资质 taxpayer_aptitude
        item['taxpayer_aptitude'] = ''.join(
            html.xpath('//td[text()="纳税人资质"]/following-sibling::td[1]//text()')).strip()
        # 人员规模  employees_num
        item['employees_num'] = ''.join(
            html.xpath('//td[text()="人员规模"]/following-sibling::td[1]//text()')).strip()
        # 实缴资本  paid_capital
        item['paid_capital'] = ''.join(
            html.xpath('//td[text()="实缴资本"]/following-sibling::td[1]//text()')).strip()
        # 登记机关 registration_authority
        item['registration_authority'] = ''.join(
            html.xpath('//td[text()="登记机关"]/following-sibling::td[1]//text()')).strip()
        # 参保人数 insured_num
        item['insured_num'] = ''.join(
            html.xpath('//td[text()="参保人数"]/following-sibling::td[1]//text()')).strip()
        # 英文名称 company_enname
        company_enname = html.xpath('//td[text()="英文名称"]/following-sibling::td[1]//text()')
        item['company_enname'] = company_enname[-1] if len(company_enname) != 0 else '-'
        # 注册地址  registered_address
        registered_address = html.xpath('//td[text()="注册地址"]/following-sibling::td[1]//text()')
        item['registered_address'] = registered_address[0] if len(registered_address) != 0 else '-'
        # 经营范围  operation_scope
        item['operation_scope'] = ''.join(html.xpath(
            '//td[text()="经营范围"]/following-sibling::td[1]//span[contains(@class,"js-full-container")]//text()'
        )).strip()
        # --------------------股东信息(大股东)--------------------
        # 大股东 big_holder
        item['big_holder'] = ''.join(html.xpath(
            '//span[contains(text(),"大股东")]/preceding-sibling::*/text()')).strip()
        # 大股东链接  big_holder_id
        item['big_holder_id'] = ''.join(html.xpath(
            '//span[contains(text(),"大股东")]/preceding-sibling::*/@href')).strip(
            'https://www.tianyancha.com/human/').strip()
        # 大股东出资 big_holder_investment
        item['big_holder_investment'] = ''.join(html.xpath(
            '//span[contains(text(),"大股东")]/../../../following-sibling::td[2]//text()')).strip()
        # 大股东出资比例  big_holder_investment_rate
        item['big_holder_investment_rate'] = ''.join(html.xpath(
            '//span[contains(text(),"大股东")]/../../../following-sibling::td[1]//text()')).strip()
        # 大股东出资时间  big_holder_investment_date
        item['big_holder_investment_date'] = ''.join(html.xpath(
            '//span[contains(text(),"大股东")]/../../../following-sibling::td[3]//text()')).strip()
        # --------------------税务评级--------------------
        # 税务评级 tax_level
        item['tax_level'] = ''.join(html.xpath(
            '//th[contains(text(),"纳税评级")]/../../following-sibling::*/tr[1]/td[3]/text()')).strip()
        # --------------------融资历史--------------------
        # 融资历史  financing_info
        financing_info, financing = [], {}
        rongzis = html.xpath('//div[contains(@id,"container_rongzi")]//tbody/tr')
        for rz in rongzis:
            financing['01num'] = ''.join(rz.xpath('./td[1]/text()'))  # 序号 num
            financing['02date'] = ''.join(rz.xpath('./td[2]/text()'))  # 时间  date
            financing['03rounds'] = ''.join(rz.xpath('./td[3]/text()'))  # 轮次 rounds
            financing['04appraisement'] = ''.join(rz.xpath('./td[4]/text()'))  # 估值 valuation
            financing['05sum_of_money'] = ''.join(rz.xpath('./td[5]/text()'))  # 金额  sum
            financing['06rate'] = ''.join(rz.xpath('./td[6]/text()'))  # 比例 rate
            financing['07investor'] = ','.join(rz.xpath('./td[7]//text()'))  # 资方  investor
            financing_info.append(deepcopy(financing))
        item['financing_info'] = financing_info
        # 是否存在年报
        yeaReport = ''.join(html.xpath('//div[contains(text(),"公司年报")]/span[contains(@class,"itemnumber")]/text()'))
        item['yeaReport'] = 0 if len(yeaReport) == 0 else 1
        # 是否存在分支机构
        branch = ''.join(html.xpath('//div[contains(text(),"分支机构")]/span[contains(@class,"itemnumber")]/text()'))
        item['branch'] = 0 if len(branch) == 0 else 1
        return item

    # 天眼查分支机构信息
    def branch_parse(self, response):
        items, item, html = [], {}, etree.HTML(response)
        seletors = html.xpath('//tbody/tr')
        for seletor in seletors:
            # 被投资公司名称
            item['branch_company_name'] = ''.join(seletor.xpath('./td[2]//a[@class="link-click"]/text()'))
            # 分支公司id
            item['branch_company_id'] = ''.join(
                seletor.xpath('./td[2]//a[@class="link-click"]/@href')).strip('https://www.tianyancha.com/company/')
            # 法定代表或者负责人
            item['branch_legal_person'] = ''.join(seletor.xpath('./td[3]//text()'))
            # 注册时间
            item['branch_reg_date'] = ''.join(seletor.xpath('./td[4]//text()'))
            # 状态
            item['branch_status'] = ''.join(seletor.xpath('./td[5]//text()'))
            items.append(deepcopy(item))
        total_page = ''.join(
            html.xpath('//a[contains(@class,"next")]/../preceding-sibling::li[1]/a/text()')).strip().replace('...', '')
        return (1, items) if not total_page.isdigit() else (int(total_page), items)

    # 天眼查股东信息解析
    def stockholder_parse(self, response):
        items, item, html = [], {}, etree.HTML(response)
        seletors = html.xpath('//tbody/tr')
        for seletor in seletors:
            # holder_name  股东名称
            item['holder_name'] = ''.join(seletor.xpath('./td[2]//div[contains(@class,"dagudong")]/a/text()')).strip()
            # holder_id	股东id
            item['holder_id'] = ''.join(seletor.xpath('./td[2]//div[contains(@class,"dagudong")]/a/@href')).replace(
                'https://www.tianyancha.com/human/', '').replace('https://www.tianyancha.com/company/', '').strip()
            # investment_proportion 出资比例
            item['investment_proportion'] = ''.join(
                seletor.xpath('./td[3]//span[contains(@class,"num-investment-rate")]/text()')).strip()
            # investment_amount 认缴出资
            item['investment_amount'] = ''.join(seletor.xpath('./td[4]/div/span/text()')).strip()
            # investment_date 出资时间
            item['investment_date'] = ''.join(seletor.xpath('./td[5]/div/span/text()')).strip()
            items.append(deepcopy(item))
        total_page = ''.join(
            html.xpath('//a[contains(@class,"next")]/../preceding-sibling::li[1]/a/text()')).strip().replace('...', '')
        return (1, items) if not total_page.isdigit() else (int(total_page), items)

    # 天眼查对外投资解析
    def investment_parse(self, response):
        items, item, html = [], {}, etree.HTML(response)
        seletors = html.xpath('//tbody/tr')
        for seletor in seletors:
            # 被投资公司名称
            item['invested_company_name'] = ''.join(seletor.xpath('./td[2]//a/text()'))
            # 被投资公司id
            item['invested_company_id'] = ''.join(
                seletor.xpath('./td[2]//a/@href')).strip('https://www.tianyancha.com/company/')
            # 被投资法定代表人
            item['legal_person'] = ''.join(seletor.xpath('./td[3]//a/@title'))
            # 注册资本
            item['registered_capital'] = ''.join(seletor.xpath('./td[4]/span/text()'))
            # 投资占比
            item['investment_proportion'] = ''.join(
                seletor.xpath('./td[5]/span//text()'))
            # 注册时间
            item['registered_date'] = ''.join(seletor.xpath('./td[6]/span/text()'))
            # 状态
            item['status'] = ''.join(seletor.xpath('./td[7]/span[contains(@class,"num")]/text()'))
            items.append(deepcopy(item))
        total_page = ''.join(
            html.xpath('//a[contains(@class,"next")]/../preceding-sibling::li[1]/a/text()')).strip().replace('...',
                                                                                                             '')
        return (1, items) if not total_page.isdigit() else (int(total_page), items)

    # 天眼查年报解析
    def annualreport_parse(self, response):
        item, html = {}, etree.HTML(response)
        item['title'] = ''.join(html.xpath('//h1[@class="report_all_title"]//text()')).strip()
        # ---------------------企业基本信息---------------------
        # 注册号
        item['reg_code'] = ''.join(html.xpath('//td[text()="注册号"]/following-sibling::td[1]/text()')).strip()
        # 信用代码
        item['social_credit_code'] = ''.join(
            html.xpath('//td[contains(text(),"信用代码")]/following-sibling::td[1]/text()')).strip()
        # 企业名称
        item['company_name'] = ''.join(html.xpath('//td[text()="企业名称"]/following-sibling::td[1]/text()')).strip()
        # 企业联系电话
        item['phone'] = ''.join(html.xpath('//td[text()="企业联系电话"]/following-sibling::td[1]/text()')).strip()
        # 邮政编码
        item['postalcode'] = ''.join(html.xpath('//td[text()="邮政编码"]/following-sibling::td[1]/text()')).strip()
        # 企业经营状态
        item['status'] = ''.join(html.xpath('//td[text()="企业经营状态"]/following-sibling::td[1]/text()')).strip()
        # 从业人数
        item['employee_nums'] = ''.join(html.xpath('//td[text()="从业人数"]/following-sibling::td[1]/text()')).strip()
        # 电子邮箱
        item['email'] = ''.join(html.xpath('//td[text()="电子邮箱"]/following-sibling::td[1]/text()')).strip()
        # 是否有网站或网店
        item['website'] = ''.join(html.xpath('//td[text()="是否有网站或网店"]/following-sibling::td[1]/text()')).strip()
        # address
        item['address'] = ''.join(html.xpath('//td[text()="企业通信地址"]/following-sibling::td[1]/text()')).strip()
        # ---------------------企业资产状况信息---------------------
        # 资产总额
        item['total_assets'] = ''.join(html.xpath('//td[text()="资产总额"]/following-sibling::td[1]/text()')).strip()
        # 所有者权益合计
        item['total_equity'] = ''.join(html.xpath('//td[text()="所有者权益合计"]/following-sibling::td[1]/text()')).strip()
        # 销售总额
        item['total_salesquity'] = ''.join(html.xpath('//td[text()="销售总额"]/following-sibling::td[1]/text()')).strip()
        # 利润总额
        item['total_profit'] = ''.join(html.xpath('//td[text()="利润总额"]/following-sibling::td[1]/text()')).strip()
        # 营业总收入中主营业务收入
        item['main_income'] = ''.join(html.xpath('//td[text()="营业总收入中主营业务收入"]/following-sibling::td[1]/text()')).strip()
        # 净利润
        item['net_profit'] = ''.join(html.xpath('//td[text()="净利润"]/following-sibling::td[1]/text()')).strip()
        # 纳税总额
        item['total_tax'] = ''.join(html.xpath('//td[text()="纳税总额"]/following-sibling::td[1]/text()')).strip()
        # 负债总额
        item['total_liabilities'] = ''.join(html.xpath('//td[text()="负债总额"]/following-sibling::td[1]/text()')).strip()
        # ---------------------社保信息---------------------
        # 城镇职工基本养老保险
        item['endowment_insurance'] = ''.join(
            html.xpath('//td[text()="城镇职工基本养老保险"]/following-sibling::td[1]/text()')).strip()
        # 职工基本医疗保险
        item['medical_insurance'] = ''.join(
            html.xpath('//td[text()="职工基本医疗保险"]/following-sibling::td[1]/text()')).strip()
        # 生育保险
        item['maternity_insurance'] = ''.join(html.xpath('//td[text()="生育保险"]/following-sibling::td[1]/text()')).strip()
        # 失业保险
        item['unemployed_insurance'] = ''.join(
            html.xpath('//td[text()="失业保险"]/following-sibling::td[1]/text()')).strip()
        # 工伤保险
        item['injury_insurance'] = ''.join(html.xpath('//td[text()="工伤保险"]/following-sibling::td[1]/text()')).strip()
        return item

    # 代码中心解析模块
    def code_parse(self, response):
        item, data = {}, []
        html = etree.HTML(response) if response != '' else etree.HTML('Null')
        selectors = html.xpath('//div[contains(@class,"result")]/div[contains(@class,"has-img")]')
        for selector in selectors:
            # 获取公司名称
            company_names = selector.xpath('./div/a/h3//text()')
            item['company_name'] = (''.join(company_names)).strip() if len(company_names) != 0 else '无'
            # 获取url
            urls = selector.xpath('./div/a/@title')
            item['url'] = 'https://ss.cods.org.cn' + str(urls[0]).strip() if len(urls) != 0 else '无'
            # 经营状态
            states = selector.xpath('./div[@class="tit"]/a/em/text()')
            try:
                item['state'] = ((str(states[0]).strip()).split('：'))[-1] if len(states) != 0 else '无'
            except:
                item['state'] = '无'
            # 信用代码
            codes = selector.xpath(
                './div[@class="info"]/h6[contains(text(),"信用代码")]//following-sibling::*[1]/text()')
            item['code'] = codes[0] if len(codes) != 0 else '无'
            # 成立时间
            founding_times = selector.xpath(
                './div[@class="info"]/h6[contains(text(),"成立时间")]//following-sibling::*[1]/text()')
            item['founding_time'] = founding_times[0] if len(founding_times) != 0 else '无'
            # 登记号
            regist_nums = selector.xpath(
                './div[@class="info"]/h6[contains(text(),"登记号")]//following-sibling::*[1]/text()')
            item['regist_num'] = regist_nums[0] if len(regist_nums) != 0 else '无'
            # 注册地址
            regist_adds = selector.xpath(
                './div[@class="info"]/h6[contains(text(),"注册地址")]//following-sibling::*[1]/text()')
            item['regist_add'] = regist_adds[0] if len(regist_adds) != 0 else '无'
            # 经营期限
            operate_times = selector.xpath(
                './div[@class="info"]/h6[contains(text(),"经营期限")]//following-sibling::*[1]/text()')
            item['operate_time'] = operate_times[0] if len(operate_times) != 0 else '无'
            # 历史名称
            history_names = selector.xpath(
                './div/p[contains(text(),"历史名称")]//text()')
            item['history_name'] = ''.join(history_names).strip('历史名称：') if len(
                ''.join(history_names)) != 0 else '无'
            data.append(deepcopy(item))
        return data
