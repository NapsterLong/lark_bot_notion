from datetime import datetime
import logging
import time
from http.cookies import SimpleCookie
import random
from urllib.parse import parse_qs, urlparse

import requests

from article.ArticlesInfo import ArticlesInfo
from article.auto_gc import all_exist_articles, auto_gc_process
from lark_util import article_collect_config
from message import reply_msg

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
def get_related_article_depth(article_url, article_info):
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


def get_article_read_num(article_url, cookie):
    cookie_obj = SimpleCookie()
    cookie_obj.load(cookie)
    appmsg_token = cookie_obj.get("appmsg_token").value
    # 登录微信PC端获取文章信息
    test = ArticlesInfo(appmsg_token, cookie)
    read_num, like_num, old_like_num = test.read_like_nums(article_url)
    return read_num


def auto_collect(cookie, message_id):
    auto_cw(cookie, message_id, "wechat")
    auto_cw(cookie, message_id, "normal")


def check_meet_req(read_num, read_num_max, article_info, a_type):
    if a_type == "wechat":
        if read_num > read_num_max:
            today_ts = datetime.today().timestamp()
            article_ts = float(article_info.get("create_timestamp"))
            if today_ts - article_ts <= 15 * 24 * 60 * 60:
                return True
            else:
                return False
        else:
            return False
    else:
        return True if read_num > read_num_max else False


def auto_cw(cookie, message_id, a_type):
    if a_type == "wechat":
        max_count = 10
        read_num_max = 20000
        prefix = "公众号素材"
    else:
        max_count = 20
        read_num_max = 10000
        prefix = "普通素材"
    logging.info("auto_cw start")
    if message_id:
        reply_msg({"text": f"{prefix}开始收集中..."}, "text", message_id, article_collect_config)
    all_articles = all_exist_articles()
    exist_urls = []
    for d in all_articles:
        if d.fields.get("状态") == "已发布" and "公众号" in d.fields.get("发布渠道") and d.fields.get("标题分类") in (
                "夫妻忠诚冲突", "特殊爱情冲突", "家庭伦理冲突", "婆媳冲突"):
            exist_urls.append([d.fields.get("文章链接").get("link").strip(), d.fields.get("素材保存时间")])
    exist_urls = sorted(exist_urls, key=lambda x: x[1], reverse=True)[:5]
    urls_queue = []
    for eu in exist_urls:
        article_url = eu[0]
        urls_queue.extend(get_related_article_depth(article_url, get_article_info(article_url)))
        time.sleep(5)
    success_urls = []
    failed_times = 0
    loop_times = 0
    success_flag = True
    while len(success_urls) <= max_count:
        url = urls_queue.pop(0)
        loop_times += 1
        logging.info(f"循环{loop_times}:{url}")
        if loop_times >= 100:
            success_flag = False
            break
        try:
            article_info = get_article_info(url)
            read_num = get_article_read_num(url, cookie)
            if check_meet_req(read_num, read_num_max, article_info, a_type):
                res = auto_gc_process(url)
                if res:
                    success_urls.append(url)
                    if message_id:
                        reply_msg({"text": f"{prefix}{len(success_urls)}已整理完成!"}, "text", message_id,
                                  article_collect_config)
                    else:
                        print(f"{prefix}{len(success_urls)}已整理完成:{url}")
            else:
                time.sleep(10)
            related_urls = get_related_article_depth(url, article_info)
            urls_queue.extend(related_urls)
        except Exception as e:
            logging.exception(e)
            failed_times += 1
            if failed_times >= 5:
                success_flag = False
                break
            continue
    if message_id:
        reply_msg({"text": f"全部{prefix}已整理完成!" if success_flag else f"{prefix}整理失败!"}, "text", message_id,
                  article_collect_config)
    else:
        print(f"全部{prefix}已整理完成!" if success_flag else f"{prefix}整理失败!")
    logging.info("auto_cw done")


if __name__ == '__main__':
    test_url = "https://mp.weixin.qq.com/s?__biz=MzIyMjEwNzMzMw==&mid=2247497409&idx=2&sn=d180a28d38d8090fd657b7727bb42ddd&chksm=e9adc246fc3e98bf3c41958e436c4af8f4196b206c8b43bb5652d3e7fa1bd75a48d48de5fa81&scene=132&exptype=timeline_recommend_article_extendread_samebiz&show_related_article=1&subscene=0&scene=132#wechat_redirect"
    # print(json.dumps(get_article_info(test_url), ensure_ascii=False))
    cookie = "_qimei_uuid42=18211143937100ec94587099cd816f3bc010e8bd23; _qimei_fingerprint=423d21b72aa8eb2715929af85cfdb2c5; _qimei_q36=; _qimei_h38=bafb7ba494587099cd816f3b0300000ed18211; qq_domain_video_guid_verify=1aae745debe4af95; tvfe_boss_uuid=19f9a64658de8ed9; pgv_pvid=2875795175; rewardsn=; wxtokenkey=777; wxuin=704572316; devicetype=iMacMac1412OSXOSX14.2.1build(23C71); version=13080712; lang=zh_CN; appmsg_token=1262_UHrAcSkBVu4gdAn0oVx7gaKu0Law0CcqYEozjOf74Du1yp9s2ASk8KIyZVYRQ6TqIvTj23JW1cdQpzOJ; pass_ticket=mf1Au92SNYHFDqQk91SxYmg781lMCKY4/kmRjQkUHIyVNk0YCbHzRy1usyfy+EF2UNhk6g332dLoxnlvFTOh2g==; wap_sid2=CJzX+88CEooBeV9IQkh0Ql95emR1NU9oWjBTaEZCYk1pYzFRRG5UelBWc1hscG9Jb2tWY2Z6Y0pldV85X0pyV0VtbGZIMnIyNGh6WjlvZWt0R2FhZ096QTRISE5DcE4tOFI0cHdfNlgxTWRiLURXSGtsS3J2dElleElBMW4xcXNIdkUxbEx4NjRLR2JNc1NBQUF+MNap9q8GOA1AAQ=="
    # print(get_article_read_num(test_url, cookie))
    auto_cw(cookie, "", "wechat")
