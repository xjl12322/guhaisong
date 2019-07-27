# -*-coding: utf-8-*-
# -*-coding: utf-8-*-
import pymysql
import xlrd





def getDatabase():
    return pymysql.connect(host="47.97.18.252", port=3306, user="ecms",
                           passwd="", db="test", use_unicode=True, charset="utf8")
    # connect = pymysql.Connect(
    #             host='rm-bp108682nces7278eqo.mysql.rds.aliyuncs.com',
    #             port=3306,
    #             user='year2001',
    #             passwd='Pachong0920',
    #             db='spider',
    #             charset='utf8'
    #         )
    # return connect


def getUrls(content):
    keyword = content.get("keyword") if content.get("keyword") else ""
    # url = content.get("url") if content.get("url") else ""
    # province = content.get("province") if content.get("province") else ""
    # city = content.get("city") if content.get("city") else ""
    # area = content.get("area") if content.get("area") else ""





    sql = "INSERT INTO baidu_ranking(keyword) VALUES (%s)"
    sql1 =  "select keyword from baidu_ranking where keyword=%s"
    param = (keyword)
    cursor = conn.cursor()
    print("# # # # # syncNews start # # # # ")
    try:
        num = cursor.execute(sql1, param)
        if num != 1:
            result = cursor.execute(sql, param)
            if (result):
                noticeId = cursor.lastrowid
                conn.commit()
                print("第{}条插入成功".format(noticeId))
        else:
            print("{}： 存在".format(keyword))
    except Exception as e:
        print("syncNews Exception ", e)
        conn.rollback()



def read():
    import xlrd
    book = xlrd.open_workbook('lingshi.xls')
    sheet = book.sheet_by_index(0)
    rowCount = sheet.nrows
    for x in range(2400, rowCount):
        # row = sheet.row_values(1)
        # col=sheet.col_values(1)
        dicts = {}
        keyword = sheet.cell(x, 0).value
        # province = sheet.cell(x, 1).value
        # city = sheet.cell(x, 2).value
        # area = sheet.cell(x, 3).value
        # url = sheet.cell(x, 4).value
        dicts["keyword"] = keyword.strip()
        # dicts["province"] = province.strip()
        # dicts["city"] = city.strip()
        # dicts["area"] = area.strip()
        # dicts["url"] = url.strip()
        if not dicts["keyword"] == "":
            # print(dicts)
            getUrls(dicts)
if __name__ == "__main__":
    conn = getDatabase()
    read()
