# coding=utf-8
from Unit import Create_font
from Unit import Get_text
from Unit import Create_pic
from Unit import Img_api
from Unit import Save


def run(code):
    if code is not None:
        items, item = {}, {}
        # 检测字体是否存在
        res = Save.repeated_detect(code)
        if res == 'yes':
            # 生成字体
            if Create_font.Create(code):
                # 获取映射字体文本
                text = Get_text.get(code)
                if text is not None:
                    # 写入文件
                    Create_pic.Create(text, code)
                    # 进入识别
                    ret = Img_api.Distinguish()
                    try:
                        for i in range(len(text)):
                            item[text[i]] = ret[i]
                    except:
                        pass
                    finally:
                        items['_id'] = code
                        items['mapping'] = item
                        Save.save_font(items)
                        return item
        else:
            item = Save.search(code)
            return item


if __name__ == '__main__':
    code = '07ca664d'
    item = run(code)
    print(item)
