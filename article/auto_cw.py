import random
import time
from pprint import pprint
from urllib.parse import parse_qs, urlparse, quote

import requests
import random
from urllib.parse import parse_qs, urlparse, quote

import requests

from article.ArticlesInfo import ArticlesInfo

article_info_datas = {}


def get_base_info(link):
    parsed_url = urlparse(link)
    query_params = parse_qs(parsed_url.query)
    result = {}
    for k, v in query_params.items():
        if k.startswith("amp;"):
            k = k[4:]
        result[k] = v[0]
    return result


def get_article_info(article_url):
    headers = {
        "accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "cache-control": "max-age=0",
        "if-modified-since": "Fri, 1 Mar 2024 21:22:29 +0800",
        "sec-ch-ua": '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": '"macOS"',
        "sec-fetch-dest": "document",
        "sec-fetch-mode": "navigate",
        "sec-fetch-site": "none",
        "sec-fetch-user": "?1",
        "upgrade-insecure-requests": "1",
    }
    params = {"f": "json"}
    resp = requests.get(article_url, headers=headers, params=params)
    downloaded = resp.json()
    return downloaded


# https://mp.weixin.qq.com/s?__biz=MzIyMjEwNzMzMw==&mid=2247497409&idx=2&sn=d180a28d38d8090fd657b7727bb42ddd&chksm=e92b1a1537ae5cc27ada66b58bd6ff735f5efe126ed3fe79fe1c88b21c00bb1751b567d795d7&scene=132&exptype=timeline_recommend_article_extendread_samebiz#wechat_redirect
def get_related_article_depth(article_url):
    headers = {
        "accept": "*/*",
        "accept-language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7",
        "sec-ch-ua": "\"Not A(Brand\";v=\"99\", \"Google Chrome\";v=\"121\", \"Chromium\";v=\"121\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"macOS\"",
        "sec-fetch-dest": "empty",
        "sec-fetch-mode": "cors",
        "sec-fetch-site": "same-origin",
        "x-requested-with": "XMLHttpRequest"
    }
    related_article_url = "https://mp.weixin.qq.com/mp/relatedarticle"

    base_info = get_base_info(article_url)
    if base_info and base_info.get("__biz"):
        pass
    else:
        article_info = get_article_info(article_url)
        link = article_info.get("link")
        base_info = get_base_info(link)

    params = {
        "action": "getlist",
        "article_url": article_url,
        "__biz": base_info.get("__biz", ""),
        "mid": base_info.get("mid", ""),
        "idx": base_info.get("idx", ""),
        'has_related_article_info': '0',
        'is_pay': '0',
        'is_from_recommand': '1',
        'scene': '132',
        'subscene': '132',
        'is_open_comment': 'undefined',
        'wxtoken': '777',
        'x5': '0',
        'f': 'json'}
    res = requests.get(related_article_url, params=params, headers=headers)
    res = res.json()
    related_article_list = res.get("list")
    related_article_urls = []
    for info in related_article_list:
        related_article_urls.append(info.get("url"))
    return related_article_urls


def get_article_read_num(article_url):
    # 登录微信PC端获取文章信息
    appmsg_token = "1262_dH91DL2jvRdlGyHOGUdsyVeeQHgocQKR75W8daw2XELd3BAG5cYuceomgX3faO4jybJPrvpfb1jTOu42"
    cookie = "rewardsn=; wxtokenkey=777; wxuin=704572316; devicetype=iMacMac156OSXOSX14.4build(23E214); version=13080712; lang=zh_CN; appmsg_token=1262_2nTCK658eFdmyY5VcUXLeTkbsHuqbGAbYibHb7XQgg-Rxi9vqYFkh43UFyBn0IfRGx_v6xlT2QogdHzc; pass_ticket=jrt/NF85YGyoCiMxTNIPMq7J2mINlMUPh1mGqfNCZ6OyUwh4ypl4yMYgFp3uDAxctLwUAXW53fvg4AIj69ssdg==; wap_sid2=CJzX+88CEooBeV9IR29yMlhWcHVjcmlES3o3VUFvV0lrd3RsNHRsRnZqTVpORDBuUFFDZjJENFA4Y3FwemlLQlVJT0xCeDVSdEw5YVJtU3BLa3VvODk5OV9xMEpzT1lTT2VQVHlTbFR5a0J5cjF5YWVNdDhNbFdJelVJSVBoeVVtZGJtVFI5cmZsa184c1NBQUF+MK2V9a8GOA1AAQ=="
    test = ArticlesInfo(appmsg_token, cookie)
    read_num, like_num, old_like_num = test.read_like_nums(article_url)
    return read_num


if __name__ == '__main__':
    test_url = "https://mp.weixin.qq.com/s?__biz=MzIyMjEwNzMzMw==&mid=2247497409&idx=2&sn=d180a28d38d8090fd657b7727bb42ddd&chksm=e9adc246fc3e98bf3c41958e436c4af8f4196b206c8b43bb5652d3e7fa1bd75a48d48de5fa81&scene=132&exptype=timeline_recommend_article_extendread_samebiz&show_related_article=1&subscene=0&scene=132#wechat_redirect"
    # print(json.dumps(get_article_info(test_url), ensure_ascii=False))
    print(get_article_read_num(test_url))
