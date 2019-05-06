# coding=utf-8
from Unit import Parse
from Config import config
import re


def get(code):
    svg_url = config.svg_url.format(code[:2], code)
    response = Parse._request(svg_url)
    if response is not None:
        font_list = re.findall('<glyph glyph-name="(.*?)" unicode="', response)
        # 剔除“x”
        fonts = font_list[1:]
        words = ''.join(fonts)
        return words


if __name__ == '__main__':
    code = 'beda24e5'
    get(code)
