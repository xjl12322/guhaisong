import re

# ccc = ""
# a = index_node.split()
# # print(a)
# for x in a:
#     if len(x)>1:
#         ccc += x +"<br/>"
# print(ccc)
# print(index_node.split("<br\>"))



# source = re.search(r".*?(d{4}-d{1,2}-d{1,2}).*?", index_node,re.S).group(1)
# source1 =re.search(r".*?(d{4}-d{1,2}-d{1,2}).*?", index_node,re.S)
# source = re.match(r".*?：.*?", index_node,re.DOTALL)
# source = source.replace("：", "", 1).strip()
# print(source)
# print(index_node)
# out = re.search(r'''.*?(<p class="arc-xgyd".*?style=.*?>相关阅读：.*?)</div>''', index_node,re.DOTALL)
# print(out.group(1))
# print("111111111111111111111111111111111")
# out = re.sub(out.group(1), "", index_node, re.DOTALL)
# print(out)
# out = re.sub(out1.group(1),"",index_node,re.S)
# print(out)
# os.system("scrapy crawl school_aoshu_com_or_province".split())
# os.system("scrapy crawl school_zhongkao_com_or_province".split())
# os.system("scrapy crawl college_gaokao_com_spelist".split())
# os.system("scrapy crawl college_gaokao_com_schlist".split())

# os.system("scrapy crawl school_liuxue360_com_de_html".split())
# os.system("scrapy crawl eduei_com_emba".split())
# os.system("scrapy crawl eduei_com_mba".split())

a =    '''<a class="info-pic" href="http://mobile.zol.com.cn/712/7120164.html"><img onerror="javascript:this.src='https://icon.zol-img.com.cn/public/nopic.jpg'" alt="Redmi Note7 Pro发布 四款新品你Care谁" .src="https://article-fd.zol-img.com.cn/t_s200x150/g2/M00/0F/05/ChMlWlyPVBuIEFItAAHejeZxBAoAAI3LgABnowAAd6l054.png" width="200" height="150" src="https://article-fd.zol-img.com.cn/t_s200x150/g2/M00/0F/05/ChMlWlyPVBuIEFItAAHejeZxBAoAAI3LgABnowAAd6l054.jpg"></a>'''
b = '2013年05月28日 17:40 　 来源：深港在线　 　 【大 中 小】 【打印】【关闭】'


c = '''

              2014年10月29日 16:11 来源：互联网  







          '''
source = re.search(r".*?来源：(.*?)\s", c,re.S).group(1)
print(source,"dddd")

ff = '死电脑,色看,好发怕看,结婚,去啊'
ccc= ff.split(",")
print(ccc)
for x,b in enumerate(ccc):
    # print(x,b)
    if len(b)>=3:
        ccc.remove(ccc[x])
print(",".join(ccc))



