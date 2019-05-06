# coding=utf-8
from PIL import Image
from PIL import ImageDraw
from PIL import ImageFont


def Create(text, code):
    ttfont = ImageFont.truetype("./Static/Font/tyc-num.ttf".format(code), 20)
    im = Image.open("./Static/Img/base.png")
    draw = ImageDraw.Draw(im)
    num, rows, hnum = 0, 0, 0
    # 最后一行少于一定数量，识别有误差
    if (len(text) - 21) % 22 <= 10:
        text = text + text[-1:] * 10
    for string in text:
        if rows <= 20:
            draw.text((num + 10, hnum + 10), string, fill=(0, 0, 0), font=ttfont)
            rows += 1
            num += 25
        else:
            hnum += 25
            rows, num = 0, 0
            draw.text((num + 10, hnum + 10), string, fill=(0, 0, 0), font=ttfont)
            num += 25
    im.save('./Static/Img/sample.png')


if __name__ == '__main__':
    pass
