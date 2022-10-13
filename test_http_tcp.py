import requests

resp = requests.get('http://192.168.9.28:9208/super/platform/cam/get/org?gbCode=34020000003000000123&pageNum=2&pageIndex=50')
body = resp.content