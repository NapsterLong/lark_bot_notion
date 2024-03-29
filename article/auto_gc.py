import datetime
import logging
import math
import os
# import sys
# sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import random
import re

import requests
from openai import OpenAI
from trafilatura import extract
from zhipuai import ZhipuAI

from doc import bitable_insert_record, bitable_list_records_all
from lark_util import article_collect_config
from message import reply_msg

model_name = "glm-4"
app_token = "ZNe3bCaQaaFwZrsrqJXcfOBPnah"
table_id = "tblhHroNH6EkMCIL"

if model_name == "gpt-4-turbo-preview":
    proxy_url = "http://127.0.0.1"
    proxy_port = "7890"

    os.environ["http_proxy"] = f"{proxy_url}:{proxy_port}"
    os.environ["https_proxy"] = f"{proxy_url}:{proxy_port}"

prompts = {
    "gpt-4-turbo-preview": {
        "step1": """
        文章内容：{text}
        请梳理以上文章的故事框架,按照下面的要求进行梳理：详细的人物背景介绍、详细具体情节发展。要求介绍要尽可能的详细，至少500字以上
        """,
        "step2": """
        [人物背景和故事情节]：{text}

        请以上面的人物背景介绍和具体情节发展，生产一个家庭情感故事，要求如下：
        1.字数要求1500字左右；
        2.全文要以第一人称口吻进行描述，要用更多口语化的对话语言，要符合真实性，符合家庭关系矛盾的内容，要更多描述行为、动作，减少内心活动的描述，语言朴实，不要有华丽的辞藻，要让人感觉真实，让读者有兴趣阅读，更容易阅读；
        3.开篇要更多介绍人物背景，年龄，工作和收入情况，高潮部分要更多具体细节矛盾冲突；
        4.情节增加更多的具体细节矛盾冲突；
        5.新故事中角色的名字和年龄需要进行合理的修改替换；
        """,
        "step3": "",
        "step4": """
        请根据以下要求在原标题的基础上改成生成一个新的文章标题，要求如下：
        1. 标题中尽可能包含数字；
        2. 标题中尽可能口语化，需要让人感觉意外震惊反常，有强烈反差或对比的效果；
        3. 标题中尽可能包含金钱、性暗示、死亡、反常、幻想、暴力等信息；
        4. 只输出标题内容，禁止输出其他；

        一些参考的例子：
        1. 女婿错把52岁岳母当成老婆，岳母很满足，女儿夸他干的漂亮
        2. 我26岁，为了改命，主动被陌生男人折腾一晚，花费26W，才发现背后全是骗局。
        3. 26岁的我，花费26W，只为改命，主动让陌生男折腾一晚，结果人钱双失.

        原标题：{title}
        输出：
        """,
    },
    "glm-4": {
        "step1": """
        文章内容：：{text}
        请输出上面故事中详细的人物背景介绍、详细具体情节发展。要求介绍要尽可能的详细，至少500字以上
        """,
        "step2": """
        [人物背景和故事情节]：：{text}

        请以上面的人物背景介绍和具体情节发展，输出一个完整的家庭情感故事，要求如下：
        1. 全文要以第一人称口吻进行描述，要用更多口语化的对话语言，要符合真实性，符合家庭关系矛盾的内容，要更多描述行为、动作，减少内心活动的描述，语言朴实，不要有华丽的辞藻，要让人感觉真实，让读者有兴趣阅读，更容易阅读；
        2. 开篇要更多介绍人物背景，年龄，工作和收入情况，高潮部分要更多具体细节矛盾冲突；
        3. 需要增加更多细节情节，需要增加更多细节矛盾冲突；
        4. 新故事中角色的名字和年龄需要重新生成替换；
        5. 只需要输出故事，不需要额外的总结；
        6. 字数要求1000字以上；
        """,
        "step3": """
        你是一个故事细节丰富大师，请根据下面给出的部分故事情节，丰富更多的细节描写并输出，有如下要求要遵守：
        1. 要求增加更多细节描写，增加更多的字数，增加更多的细节矛盾冲突，增加更多的环境背景描写，增加更多的人物心理描写；
        2. 禁止修改故事结构，禁止增加新的内容，禁止增加新的结局；
        3. 要求更多口语化的对话语言，要符合真实性，符合家庭关系矛盾的内容
        
        部分故事情节：{text}
        """,
        "step4": """
        请根据以下要求在原标题的基础上改成生成一个新的文章标题，要求如下：
        1. 新标题中至少包含两种数字信息，可以凭空想象，比如增加年龄、薪资、金钱、时间等数字表达；
        2. 新标题尽量保持原来标题的结构，多使用大白话的近义词替换；
        3. 新标题中尽量使用口语化的短句子
        4. 先输出思考过程，然后输出输出标题内容，禁止输出其他；

        这是一些例子：
        原标题1：我哥和我嫂月入2万8，嫂子春节穿回家的大衣连吊牌都没撕，被我撞见了所有秘密，我妈得知真相特别震惊
        思考过程1：原标题只有1个数字信息，可以增加年龄信息，其他句子按照近义词和大白话短句子改写；
        新标题1：25岁的嫂子和我哥，月赚2万8，过年她带回的大衣竟标签都没拆，不小心被我揭开了真相，老妈听后都惊呆了
        

        原标题2：老公月入3万不在家，我竟花1万包养小鲜肉，6个月后的惊天反转让我欲哭无泪!
        思考过程2：原标题已包含2个数字信息，但是句子稍长，需要做短句子改写；
        新标题2：老公月入3万，半年回来一次，我找了个小男朋友，每个月给他1万，结果报应来了

        原标题3：老婆洗澡时突然来姨妈，喊我下楼买卫生巾，忘拿钱返回，推开门看到令人无法相信的一幕
        思考过程3：原标题已不包含数字信息，可以增加年龄、金钱等数字信息，其他句子按照近义词和大白话短句子改写；
        新标题3：老婆急叫我买卫生巾，花了50块却回来目睹了1000万的背叛场面，真相让人崩溃!

        原标题4：我52岁，女儿外出，女婿酒后错把我当她老婆，让我愉悦，女儿回来后，夸女婿做的棒
        思考过程4：原标题只包含1个数字信息，可以增加年龄、金钱等数字信息，其他句子按照近义词和大白话短句子改写；
        新标题4：我妈52岁，这天我出差，老公喝多了，把我妈当成我，让我妈愉悦，我回来后，夸老公做的棒

        需要改写的标题如下：
        原标题5：{title}
        """,
        "step5": """
        # Role：
        你是标题分类器，一个专门针对文章标题进行分类的工具。
        
        # WorkFlow：
        1. 根据用户输入的标题，请以冲突的类型给这些文章分类，其中冲突的分类包含以下几种类型：
        - 夫妻忠诚冲突：包括不忠、外遇、出轨、小三、背叛、性生活、生育能力、孩子不是亲生、绿帽、离婚、爱上别人等内容；
        - 夫妻其他冲突：包括夫妻生活习惯、孩子教育、家务、沟通、消费理念等内容；
        - 婆媳冲突：包括婆婆和媳妇之间发生的冲突等内容；
        - 家庭伦理冲突：包括姐夫和小姨子不正当关系、老公和小姑子不正当关系、女婿和岳母不正当关系、媳妇和公公不正当关系、媳妇和哥哥弟弟不正当关系等内容；
        - 父母子女冲突：包括父母和孩子之间的冲突等内容：
        - 兄弟姐妹冲突：包括兄弟姐妹之间的冲突；
        - 单身家庭冲突：包括单身家庭背景下的冲突；
        - 职业职场冲突：包括职场中的各种冲突；
        - 特殊爱情冲突：包括年龄差别很大的婚姻、一夜情、嫖娼等内容
        - 其他冲突：不包含以上场景的其他冲突
        2. 首先输出推理过程，以推理过程：开头，然后输出分类结果，以结果：开头，禁止输出其他额外信息；
        3. 注意结果中只能包含以下10种值： 夫妻忠诚冲突、夫妻其他冲突、婆媳冲突、家庭伦理冲突、父母子女冲突、兄弟姐妹冲突、单身家庭冲突、职业职场冲突、特殊爱情冲突、其他冲突
        
        # Inputs
        标题：{title}
        """
    }

}

client = {
    "gpt-4-turbo-preview": OpenAI(),
    "glm-4": ZhipuAI(api_key="8190057035b41c4d5c584c2b1e5cd616.X1QSpaFAFJwkZ6nW")
}


def llm_chat(llm_client, prompt, temperature=0.7, max_tokens=2048):
    response = llm_client.chat.completions.create(
        model=model_name,
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens
    )
    return response.choices[0].message.content.strip()


re_split = re.compile("。|\n\n|？|！")


def trans(text: str):
    text = text.strip()
    sentences = re_split.split(text)
    max_sentences_length = len(sentences)
    max_para_length = len(text.split("\n\n"))
    piece_count = random.randint(3, 5)
    sentence_length = math.floor(max_sentences_length / piece_count)
    para_length = math.floor(max_para_length / piece_count)
    piece_type = "para" if 5 <= max_para_length <= 15 else "sentence"
    titles1 = ["一", "二", "三", "四", "五", "六", "七", "八"]
    titles2 = ["01", "02", "03", "04", "05", "06", "07", "08"]
    titles3 = ["①", "②", "③", "④", "⑤", "⑥", "⑦", "⑧"]
    titles = random.choice([titles1, titles2, titles3])
    output = [titles.pop(0)]
    sentence_count = 0
    para_count = 0
    sentence_flag = False
    para_flag = False
    for s in sentences:
        if sentence_flag:
            output.append(titles.pop(0))
            sentence_count = 0
            sentence_flag = False
        if para_flag:
            output.append(titles.pop(0))
            para_count = 0
            para_flag = False
        if s.strip():
            output.append(s.strip() + "。")
            sentence_count += 1
            if sentence_count >= sentence_length and piece_type == "sentence":
                sentence_flag = True
        else:
            output.append(s)
            para_count += 1
            if para_count >= para_length and piece_type == "para":
                para_flag = True
    if len(output[-1].strip()) == 1:
        output.pop(-1)
    for idx, ot in enumerate(output):
        output[idx] = ot.lstrip("。")
        if ot.startswith("”") and idx != 0:
            output[idx - 1] = output[idx - 1] + "”"
            output[idx] = ot.lstrip("”").lstrip("。")

    output_text = "\n".join(output)
    # output_text = output_text.replace("\n\n", "\n").strip()
    return output_text


def get_url_content(url):
    # downloaded = fetch_url(url)
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
    resp = requests.get(url, headers=headers, params=params)
    downloaded = resp.json()
    title = downloaded.get("title")
    content_noencode = downloaded.get("content_noencode")
    page_create_time = downloaded.get("create_time")
    output = extract(content_noencode)
    return title, output, page_create_time


def all_exist_articles():
    all_datas = bitable_list_records_all(app_token, table_id)
    return all_datas


def check_dup(url, title=""):
    all_datas = bitable_list_records_all(app_token, table_id)
    for d in all_datas:
        if d.fields.get("文章链接").get("link").strip() == url.strip():
            return True
        if d.fields.get("旧标题").strip() == title.strip():
            return True
    return False


re_number = re.compile("\d")
re_title_cls = re.compile("推理过程：(.*)\s+结果：(.*)")


def auto_gc_process(url, message_id=""):
    output = ""
    try:
        if check_dup(url):
            logging.info(f"{url},该文章素材已被收集过")
            if message_id:
                reply_msg({"text": "该文章素材已被收集过!"}, "text", message_id, article_collect_config)
            return
        llm_client = client.get(model_name)
        logging.info(f"{url},处理开始")
        title, origin_content, page_create_time = get_url_content(url)

        if check_dup(url, title):
            logging.info(f"{url},{title},该文章素材已被收集过")
            if message_id:
                reply_msg({"text": "该文章素材已被收集过!"}, "text", message_id, article_collect_config)
            return

        new_title_prompt = prompts[model_name]["step4"].format(title=title)

        for i in range(3):
            new_title = llm_chat(llm_client, new_title_prompt)
            new_title = format_title(new_title)
            if re_number.search(new_title):
                logging.info(f"{url},标题生成成功")
                break
        if new_title == "标题提取失败":
            raise ValueError("标题提取失败")

        title_cls = ""
        title_cls_prompt = prompts[model_name]["step5"].format(title=title)
        title_cls_res = llm_chat(llm_client, title_cls_prompt, temperature=0.01, max_tokens=256)
        re_res = re_title_cls.search(title_cls_res)
        if re_res:
            title_cls = re_res.groups()[1].strip("。")
        if title_cls:
            logging.info(f"{url},标题分类成功")
        else:
            logging.info(f"{url},标题分类失败")

        article_framework_prompt = prompts[model_name]["step1"].format(text=origin_content)
        article_framework = llm_chat(llm_client, article_framework_prompt)
        logging.info(f"{url},框架生成成功")

        article_prompt = prompts[model_name]["step2"].format(text=article_framework)
        article = llm_chat(llm_client, article_prompt)
        logging.info(f"{url},文章生成成功，字数：{len(article)}")
        if not message_id:
            print(f"\n{article}\n")

        if len(article) < 1000 and prompts[model_name]["step3"]:
            article_para = article.splitlines()
            remain1 = "\n".join(article_para[:1])
            partial_article = "\n".join(article_para[1:-1])
            remain2 = "\n".join(article_para[-1:])
            expand_prompt = prompts[model_name]["step3"].format(text=partial_article)
            new_partial_article = llm_chat(llm_client, expand_prompt)
            article = remain1 + new_partial_article + remain2
            logging.info(f"{url},文章扩写成功，字数：{len(article)}")
            if not message_id:
                print(f"\n{article}\n")

        output = trans(article)
        logging.info(f"{url},文章转换成功")
        if not message_id:
            print(f"\n{output}\n")
        write_database(url, title, new_title, origin_content, output, article_framework, article, title_cls,
                       page_create_time)
        logging.info(f"{url},数据库写入成功")
        if message_id:
            reply_msg({"text": "素材已整理完成!"}, "text", message_id, article_collect_config)
    except Exception as e:
        logging.exception(f"{url},素材处理失败")
        if message_id:
            reply_msg({"text": "素材处理失败!"}, "text", message_id, article_collect_config)
        return None
    return output


re_title = re.compile("新标题5：(.*)")


def format_title(new_title):
    tt = re_title.search(new_title)
    if tt:
        new_title = tt.groups()[0]
    else:
        return "标题提取失败"

    new_title = new_title.strip("\"")
    if new_title.startswith("新标题："):
        new_title = new_title[4:]
    new_title_sp = new_title.splitlines()
    new_title_sp = [s.strip() for s in new_title_sp if s.strip()]
    if len(new_title_sp) > 1:
        new_title = new_title_sp[0]
    return new_title


def write_database(
        url, title, new_title, origin_content, output, article_framework, article, title_cls, page_create_time
):
    record = {
        "文章链接": {"link": url, "text": url},
        "旧标题": title,
        "新标题": new_title,
        "旧内容": origin_content,
        "新内容": output,
        "框架": article_framework,
        "生成内容": article,
        "状态": "待发布",
        "标题分类": title_cls,
        "文章发布时间": int(datetime.datetime.strptime(page_create_time, "%Y-%m-%d %H:%M").timestamp()) * 1000
    }
    bitable_insert_record(app_token, table_id, record, article_collect_config)
