#! /usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = "X"
__date__ = "2017/11/6 20:09"




import re


def contentfilter(content):
    if content:
        content = re.sub(r"<script.+?</script>","",content,flags=re.S)
        content = re.sub(r"(?<=<)[iI][Mm][gG]","img",content)
        content = re.sub(r"P(?=>)", "p", content)
        content = re.sub(r"<div.*?>", "<div>", content)
        content = re.sub(r"<p.*?>", "<p>", content)
        content = re.sub(r"<(?!/?(p|img|br|div|hr|spilt|strong|em)).*?>","",content)
        content = re.sub(r"\xa0+?", "", content)
        content = re.sub(r'u3000+?',"",content)
        content = content.strip()
        # content = re.sub(r"<p><br><p>", "", content)
        # content = re.sub(r"<p><br><p>", "", content)
        # content = re.sub(r"<p><br/></p>", "", content)
        # content = re.sub(r"<p>\r\n<br>\r\n</p>", "", content)
        # content = re.sub(r"&nbsp;&nbsp", "", content)
        # content = re.sub(r'width="\d+"', 'width="705"', content)
        # content = re.sub("<a.*?>","",content)
        # content = re.sub(" ", "", content)
        return content
    else:
        content = ""
        return content