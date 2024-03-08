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
        1. 新标题尽量保持原来标题的结构，多使用大白话的近义词替换；
        2. 只输出标题内容，禁止输出其他；
        
        原标题：{title}
        输出：
        """,
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
    titles = ["一", "二", "三", "四", "五", "六", "七", "八"]
    output = []
    output.append(titles.pop(0))
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
    output = extract(content_noencode)
    return title, output


def check_dup(url):
    all_datas = bitable_list_records_all(app_token, table_id)
    for d in all_datas:
        if d.fields.get("文章链接").get("link").strip() == url.strip():
            return True
    return False


re_number = re.compile("\d")


def gpt_base_process(url, message_id=""):
    output = ""
    try:
        if check_dup(url):
            logging.info(f"{url},该文章素材已被收集过")
            if message_id:
                reply_msg({"text": "该文章素材已被收集过!"}, "text", message_id, article_collect_config)
            return
        llm_client = client.get(model_name)
        logging.info(f"{url},处理开始")
        title, origin_content = get_url_content(url)

        new_title_prompt = prompts[model_name]["step4"].format(title=title)

        for i in range(3):
            new_title = llm_chat(llm_client, new_title_prompt)
            new_title = format_title(new_title)
            if re_number.search(new_title):
                logging.info(f"{url},标题生成成功")
                break

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
            logging.info(f"{url},文章扩写成功")
            if not message_id:
                print(f"\n{article}\n")

        output = trans(article)
        logging.info(f"{url},文章转换成功")
        if not message_id:
            print(f"\n{output}\n")
        write_database(url, title, new_title, origin_content, output, article_framework, article)
        logging.info(f"{url},数据库写入成功")
        if message_id:
            reply_msg({"text": "素材已整理完成!"}, "text", message_id, article_collect_config)
    except Exception as e:
        logging.exception(f"{url},素材处理失败")
        reply_msg({"text": "素材处理失败!"}, "text", message_id, article_collect_config)
    return output


def format_title(new_title):
    new_title = new_title.strip("\"")
    if new_title.startswith("新标题："):
        new_title = new_title[4:]
    new_title_sp = new_title.splitlines()
    new_title_sp = [s.strip() for s in new_title_sp if s.strip()]
    if len(new_title_sp) > 1:
        new_title = new_title_sp[0]
    return new_title


def write_database(
        url, title, new_title, origin_content, output, article_framework, article
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
    }
    bitable_insert_record(app_token, table_id, record, article_collect_config)


if __name__ == "__main__":
    # gpt_base_process("https://mp.weixin.qq.com/s/QlvKtiRStvxuEp3L55Hdlw")
    a = trans("""
    
我叫王力，今年35岁，在一家软件公司上班，收入稳定。我老婆叫赵娜，跟我同岁，是个小学老师，温柔贤惠。我们结婚五年了，一直过着平静的小康生活。那天寒冷的冬夜，天空中飘着细小的雪花，赵娜在浴室里洗去了疲惫，突然大声叫我下去买卫生巾。我正蜷缩在沙发上看着电视，一听这话，心里顿时焦虑起来。这大晚上的，附近的商店早已经关门，我上哪儿去买啊？但我还是赶紧穿上外套，冲出了门。

焦急的情绪让我忘了带钱，只好又气喘吁吁地跑回家。推开浴室门的那一刻，我看到了赵娜手中的试纸，和她脸上那个镇定的、充满喜悦的笑容。

“我们要有宝宝了。”她语气温柔地说道。我愣住了，然后激动地抱住了她，感觉像是收到了一份意想不到的礼物。那天晚上，我们俩相拥入眠，聊了很久，规划着未来，满是兴奋和期待。

然而，当我把这个天大的消息告诉我爸妈的时候，我内心却开始忐忑不安。我一直知道，他们支持我们过丁克生活，担心我们有了孩子会手忙脚乱。赵娜也显得担忧，怕我爸妈会责怪我们之前没打算要孩子。

终于，紧张的时刻到了，我牵着赵娜的手，带着她去见我爸妈。我手心都是汗，心里矛盾重重，像是有十五个吊桶打水——七上八下。但出乎意料的是，我妈突然泪流满面，我爸则长叹一声。赵娜和我都愣住了，心里更加紧张了。

“妈，你怎么了？”我小心翼翼地问，心里越发地七上八下。

“没，没事，”我妈擦了擦眼泪，露出一丝微笑，“我只是太高兴了，一直盼着你们有个孩子，只是没想到会这么突然。”

“那爸，你叹什么气呢？”我又问我爸，心里还是有些不安。

我爸深深地看着我，说道：“我只是担心，你们还没准备好面对父母的角色，这个责任可重大啊。”

听到他们这么说，我和赵娜心中的石头终于落地了。我们明白了，家人的理解和支持，是我们最大的动力。

为了迎接新生命的到来，我开始忙碌起来。我陪着赵娜去做产检，我们一起挑选婴儿用品，甚至开始学习育儿知识。在这个过程中，我发现自己原来那么期待这个新生命的到来。

然而，生活总会有一些小插曲。有一天，我下班回家，发现赵娜坐在沙发上，脸色不太好。

“怎么了，娜娜？”我赶紧放下公文包，关切地问。

“今天我去产检，医生说我有点贫血，需要好好休息。”她低声说，显得有些担忧。

我一下子就急了，忙问：“那怎么办？我们要怎么帮你调理？我可不想让你和宝宝有任何闪失。”

赵娜笑了，轻轻拍了拍我的手：“没事，医生说只要注意饮食和休息就好。”

那段时间，我成了赵娜的“专职厨师”，每天变着花样给她做好吃的。而赵娜也严格按照医生的嘱咐，按时休息，保持好心情。

终于，那一天到来了。我们的宝宝顺利出生，是个可爱的女儿。看着她粉嫩的小脸，我心中充满了喜悦和感激，仿佛看到了我们幸福的未来。这段经历让我明白，家庭是我们最坚实的后盾，爱和理解是我们战胜一切困难的力量。在未来的日子里，我会更加珍惜这个家，和我的老婆孩子一起，勇敢地面对生活的每一个挑战。

    """)
    print(a)
