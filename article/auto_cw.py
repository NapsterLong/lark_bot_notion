import base64
import time
from urllib.parse import parse_qs, urlparse

import requests


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


# https://mp.weixin.qq.com/s/zajoStYWEt63xZj1-Zmtww
def get_related_article_first(article_url):
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
        'is_from_recommand': '0',
        'scene': '0',
        'subscene': '0',
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


def get_read_num(article_url):
    base_info = get_base_info(article_url)

    # 该4个参数，需要自己从抓的包里面的请求头里面去获取，
    uin = 'NzA0NTcyMzE2=='
    pass_ticket = 'FCrXGoZx3XyZic8VpKKiPF2UEgtEmd6XRXjbUfA4l1hVP2dCYT9cLcnsOfByVlt1vjofwY9t+fJ+DlfOkr2x9w=='
    appmsg_token = '1262_8slOpHWRIZe24wbQ46PBE7RDQjxolHiJeOTeRZqTRj5oPVMLQnxxM5urlKII4ceT50bUHNLwh9KEiZtw'
    key = "ffefb1af06f470698541913fbcda98e6a045e3444b729e2642d3ba75407ad99669b1f7e48f51c268d0cb6a86ff27126a3d1c3a3c246ca2dbb9de85accf3c713203ca4e5fdb00e4f310d5032541ce1a11a245e1682850f6b1f2979e6e7f6804cc0d0e2722bad1456646ba9eba779af02e848c0792bc2aa75fb8710a84476b4705"

    url = "http://mp.weixin.qq.com/mp/getappmsgext"

    cookie = "_qimei_uuid42=18211143937100ec94587099cd816f3bc010e8bd23; _qimei_fingerprint=423d21b72aa8eb2715929af85cfdb2c5; _qimei_q36=; _qimei_h38=bafb7ba494587099cd816f3b0300000ed18211; qq_domain_video_guid_verify=1aae745debe4af95; tvfe_boss_uuid=19f9a64658de8ed9; pgv_pvid=2875795175; rewardsn=; wxtokenkey=777; wxuin=704572316; devicetype=iMacMac1412OSXOSX14.2.1build(23C71); version=13080712; lang=zh_CN; appmsg_token=1262_8slOpHWRIZe24wbQ46PBE7RDQjxolHiJeOTeRZqTRj5oPVMLQnxxM5urlKII4ceT50bUHNLwh9KEiZtw; pass_ticket=FCrXGoZx3XyZic8VpKKiPF2UEgtEmd6XRXjbUfA4l1hVP2dCYT9cLcnsOfByVlt1vjofwY9t+fJ+DlfOkr2x9w==; wap_sid2=CJzX+88CEooBeV9IRFg0elZFeU90OGtpdVRIcldUaUhPeEhnN1JNMzBEQl9wS2stem9Zck9BWER0OXZSSk5PX1BSVEtBdDVYQlFpN3Q1b2MzVDdnejZ4TmFVc3VQZjFwc2VfRkpoZHAyelBBVEsxQjBwYWZZTHpjVWZCTlZFZWFrSUFOYXlSdEZITVJNc1NBQUF+MKPn8a8GOA1AAQ=="

    headers = {
        'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36 NetType/WIFI MicroMessenger/6.8.0(0x16080000) MacWechat/3.8.7(0x13080712) XWEB/1191 Flue',
        'x-requested-with': 'XMLHttpRequest',
        'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'accept': '*/*',
        'origin': 'https://mp.weixin.qq.com',
        'sec-fetch-site': 'same-origin',
        'sec-fetch-mode': 'cors',
        'sec-fetch-dest': 'empty',
        'accept-encoding': 'gzip, deflate, br',
        'accept-language': 'zh-CN,zh;q=0.9',
        'cookie': cookie
    }

    params = {
        'f': 'json',
        "uin": uin,
        "key": key,
        "pass_ticket": pass_ticket,
        "wxtoken": "777",
        'devicetype': 'iMac&nbsp;Mac14,12&nbsp;OSX&nbsp;OSX&nbsp;14.2.1&nbsp;build(23C71)',
        'clientversion': '13080712',
        "__biz": base_info.get("__biz", ""),
        "appmsg_token": appmsg_token,
        'x5': '0'
    }

    data = {'r': '0.588020539678751',
            '__biz': base_info.get("__biz", ""),
            'appmsg_type': '9',
            'mid': base_info.get("mid", ""),
            'sn': base_info.get("sn", ""),
            'idx': base_info.get("idx", ""),
            'title': '%E6%88%91%E9%AB%98%E7%83%A7%E5%9C%A8%E5%8C%BB%E9%99%A2%E8%BE%93%E6%B6%B2%EF%BC%8C%E5%A9%86%E5%AE%B66%E4%BA%BA%E6%8E%A5%E5%8A%9B%E6%89%9315%E4%B8%AA%E7%94%B5%E8%AF%9D%E9%97%AE%EF%BC%9A%E5%85%A8%E5%AE%B6%E5%B0%B1%E7%AD%89%E4%BD%A0%E5%9B%9E%E6%9D%A5%E5%81%9A%E9%A5%AD',
            'ct': '1710889141',
            'devicetype': 'iMac Mac14,12 OSX OSX 14.2.1 build(23C71)',
            'version': '13080712',
            'is_need_ticket': '0',
            'is_need_ad': '0',
            'comment_id': '3376184553257533442',
            'is_need_reward': '1',
            'both_ad': '0',
            'reward_uin_count': '125',
            'msg_daily_idx': '1',
            'is_original': '0',
            'is_only_read': '1',
            'req_id': '2201q6HQ1ygn9aNJBi8u3pgi',
            'pass_ticket': pass_ticket,
            'is_temp_url': '0',
            'item_show_type': '0',
            'tmp_version': '1',
            'more_read_type': '0',
            'appmsg_like_type': '2',
            'related_video_num': '5',
            'is_pay_subscribe': '0',
            'pay_subscribe_uin_count': '0',
            'has_red_packet_cover': '0',
            'album_id': '1296223588617486300',
            'album_video_num': '5',
            'cur_album_id': '2312186921898459137',
            'is_public_related_video': 'NaN',
            'encode_info_by_base64': 'undefined',
            'export_key': 'n_ChQIAhIQX5N5AoiwT%2F5oET2cJz%2FvVhL8AQIE97dBBAEAAAAAAA%2BaLhuaWxgAAAAOpnltbLcz9gKNyK89dVj0JgpqOkwzewQolyv3cNRhxFKexNhLTvCgiKu%2FNZnfy9RRarIiYaaSsApHL5mZB5Q0IUJ9UPkOJXqFVBoxBtWnCtVtKd8SJKyZYKfwHbni0xTLgO1mydHACHi7l8Pr0GnbvPTzkFaRSLL2wRwlTKOEqiiLmXiHjCZoj8vSC1PVERtgSUABoAPVR2q%2Fq9mh0Cuf7r%2BFd1jv3brh7CqLiAiI7yUWpd1%2Fk3dCslChCO8GU1QZFXNkcfiWibmAfpPWrszeEcgvf67V630HuaLmjhhTpWBsYPDW9A%3D%3D',
            'business_type': '0'}

    res = requests.post(url, headers=headers, data=data, params=params).json()
    print(res)

    # 获取到阅读数
    read_num = res['appmsgstat']['read_num']

    # 获取到在看书
    like_num = res["appmsgstat"]["like_num"]
    print(read_num, like_num)
    return res


if __name__ == '__main__':
    get_read_num(
        "https://mp.weixin.qq.com/s?__biz=MzIyMjEwNzMzMw==&mid=2247497247&idx=2&sn=7afd4d2e29f25dbca1c6c2354b50c997&chksm=e9c5adb1b731f81234c2f985b3de9f948c9bfd96c7eb546a38963230b3410b3fce2d7d3236e4&scene=132&exptype=timeline_recommend_article_extendread_samebiz#wechat_redirect")
    # for url in get_related_article_first("https://mp.weixin.qq.com/s/zajoStYWEt63xZj1-Zmtww"):
    #     print(url)
    #     print("------")
    #     related_urls = get_related_article_depth(url)
    #     for u in related_urls:
    #         print(u)
    #         get_read_num(u)
    #         print("======")
    #         time.sleep(5)
    #     print("==================")
