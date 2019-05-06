import pymongo
from lxml import etree
import re

coll = pymongo.MongoClient('mongodb://10.122.33.93:27017')['gov_zb']['fujian_fjggzyjy_cn']


for i in coll.find():
	_id = i['_id']
	publish_date_old = i['publish_date']
	content_html = i['content_html']
	url = i['detail_url']
	
	
	selector = etree.HTML(content_html)
	
	publish_date = selector.xpath ('//div[@class="article-title-aid"]/span//text()')

	if any(publish_date):
		publish_date = publish_date[-1]
	# publish_date = re.sub(r'\/','-',re.search(r'(\d{8}|\d{4}\/\d+\/\d{1,2})',''.join(publish_date)).group())
	# if '-' not in publish_date:
	#     publish_date = '{}-{}-{}'.format(publish_date[0:4],publish_date[4:6], publish_date[6:8])
	else:
		publish_date = None
	
	print (publish_date_old, publish_date,url)
	coll.update({'_id':_id},{'$set':{'publish_date':publish_date}})
	
	




