# coding=utf-8
from Config import config
from Unit import Parse


# 字体生成
def Create(code):
    ttf_url = config.ttf_url.format(code[:2], code)
    response = Parse._request(ttf_url, type='byte')
    if response is not None:
        # 二进制写入,存在将其覆盖,不存在创建新文件
        with open('./Static/Font/tyc-num.ttf', 'wb') as f:
            f.write(response)
        return True


if __name__ == '__main__':
    code = 'beda24e5'
    Create(code)
