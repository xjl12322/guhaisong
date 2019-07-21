#! /usr/bin/env python3
# -*- coding:utf-8 -*-
__author__ = "X"
__date__ = "2019/7/20 20:15"

#错误提示   requests.exceptions.SSLError: ("bad handshake: SysCallError(-1, 'Unexpected EOF')",)

# Python错误集(一)之SSLError
# 2018年07月26日 23:31:07 morven936 阅读数 4037
#  版权声明：本文为博主原创文章，未经博主允许不得转载。 https://blog.csdn.net/haiyanggeng/article/details/81229546
# python: 2.7
# requests: 2.19.1
#
# 最近需要向第三方发送https请求爬取数据,需要绕过SSL,但是在此过程中发生了如下错误:
#
# requests.exceptions.SSLError: (“bad handshake: SysCallError(-1, ‘Unexpected EOF’)”,)
#
# 原因:
# Requests已经移除对3DES stream cipher的支持,但是Requests有一个默认的严格的TLS 配置.
#
# 解决方法:
# 对于requests v2.12.0以下版本:

# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.poolmanager import PoolManager
# import ssl
#
# class DESAdapter(HTTPAdapter):
#     def init_poolmanager(self, connections, maxsize, block=False):
#         self.poolmanager = PoolManager(num_pools=connections,
#                                        maxsize=maxsize,
#                                        block=block,
#                                        ssl_version=ssl.PROTOCOL_TLSv1)
# s = requests.Session()
# s.mount('https://', DESAdapter())
# r = requests.get('https://some-3des-only-host.com')
# r.encoding = 'utf8'
# print r.text
# 1
# 2

# 对于requests v2.12.0及其以上版本:
#
# import requests
# from requests.adapters import HTTPAdapter
# from requests.packages.urllib3.util.ssl_ import create_urllib3_context
#
# # This is the 2.11 Requests cipher string, containing 3DES.
# CIPHERS = (
#     'ECDH+AESGCM:DH+AESGCM:ECDH+AES256:DH+AES256:ECDH+AES128:DH+AES:ECDH+HIGH:'
#     'DH+HIGH:ECDH+3DES:DH+3DES:RSA+AESGCM:RSA+AES:RSA+HIGH:RSA+3DES:!aNULL:'
#     '!eNULL:!MD5'
# )
#
#
# class DESAdapter(HTTPAdapter):
#     """
#     A TransportAdapter that re-enables 3DES support in Requests.
#     """
#     def init_poolmanager(self, *args, **kwargs):
#         context = create_urllib3_context(ciphers=CIPHERS)
#         kwargs['ssl_context'] = context
#         return super(DESAdapter, self).init_poolmanager(*args, **kwargs)
#
#     def proxy_manager_for(self, *args, **kwargs):
#         context = create_urllib3_context(ciphers=CIPHERS)
#         kwargs['ssl_context'] = context
#         return super(DESAdapter, self).proxy_manager_for(*args, **kwargs)
#
# s = requests.Session()
# s.mount('https://some-3des-only-host.com', DESAdapter())
# r = s.get('https://some-3des-only-host.com/some-path')

