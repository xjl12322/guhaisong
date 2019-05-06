# coding:utf-8
from new_spider.spiders import SpiderMeta
from new_spider import request
from new_spider import storage
import re
from new_spider.conf import gov_001,save_temp_info

class GovBuy(SpiderMeta):
    '''中国政府采购网'''
    def __init__(self):
        SpiderMeta.__init__(self)
        self.config = gov_001
        self.storage = storage.StorageManage (self.config['db_name'])
        self.headers = {
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/67.0.3396.99 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Referer': 'http://search.ccgp.gov.cn/bxsearch?searchtype=1^&page_index=1^&bidSort=0^&buyerName=^&projectId=^&pinMu=0^&bidType=0^&dbselect=bidx^&kw=^&start_time=2018^%^3A02^%^3A06^&end_time=2018^%^3A08^%^3A07^&timeType=5^&displayZone=^&zoneId=^&pppStatus=0^&agentName=',
            'Accept-Encoding': 'gzip, deflate',
            'Accept-Language': 'zh,zh-CN;q=0.9',
        }

    def load_get_html(self, url):
        if url == None:
            return
        try:
            response = request.get(url=url, headers=self.headers).content.decode('utf-8')
        except Exception as e:
            print('laod_get_html error:{}'.format(e))
        else:
            save_temp_info['content_html'] = ''.join(self._tostrings(response,'//div[@class="vF_detail_main"]'))
            save_temp_info['_id'] = self.hash_to_md5(url)
            self.storage.save_manage(save_temp_info)
            

    def load_get(self, page):
        try:
            url = 'http://search.ccgp.gov.cn/bxsearch'
    
            params = {
                'searchtype': 1,
                'page_index': page,
                'bidSort': 0,
                'buyerName': '',
                'projectId': '',
                'pinMu': 0,
                'bidType': 0,
                'dbselect': 'bidx',
                'kw': '',
                'start_time': '2019:02:19',
                'end_time': '2019:05:30',
                'timeType': 5,
                'displayZone': '',
                'zoneId': '',
                'pppStatus': 0,
                'agentName': '',
            }
            response = request.get(url=url, params=params,headers=self.headers).content.decode('utf-8')
        except Exception as e:
            print('load_get error:{}'.format(e))
        else:
            ul_li = self._tostrings(response,'//div[@class="vT-srch-result-list"]/ul/li')
            for li in ul_li:
                parse_title = {'key':'title','res':li,'rule':'//a/text()'}
                self.parse_info(parse_title)
                
                parse_status = {'key':'status','res':li,'rule':'//span/strong[1]/text()'}
                self.parse_info(parse_status)
                
                parse_publish_time = {'key':'publish_date','res':li,'rule':'//span//text()'}
                self.parse_info(parse_publish_time)
                save_temp_info['publish_date'] = re.sub(r'\.','-',''.join(re.findall(r'(\d{4}\.\d{1,2}\.\d{1,2})',save_temp_info['publish_date'])))
                
                parse_purchase_company_name = {'key':'purchase_company_name','res':li,'rule':'//span//text()'}
                self.parse_info(parse_purchase_company_name)
                save_temp_info['purchase_company_name'] = ''.join(re.findall(r'采购人：{0,1}(.*?)\|',save_temp_info['purchase_company_name']))
                
                parse_agency_name = {'key':'agency_name','res':li,'rule':'//span//text()'}
                self.parse_info(parse_agency_name)
                save_temp_info['agency_name'] = ''.join (
                    re.findall (r'代理机构：{0,1}(.*?)\|', save_temp_info['agency_name']))
                
                parse_detail_url = {'key':'detail_url','res':li,'rule':'//li/a/@href'}
                self.parse_info(parse_detail_url)
                
                self.load_get_html(save_temp_info['detail_url'])
                

    def run(self):
        task_li = [
                {'all_page': 10},
            ]
        for task in task_li:
            for page in range(1, task['all_page'] + 1):
                self.load_get(page)

    def main(self):
        self.run()

if __name__ == '__main__':
    gb = GovBuy()
    gb.main()



