import os

# import sys
# sys.path.append(os.path.dirname(os.path.dirname(__file__)))
import random
import re
import math
from openai import OpenAI
from trafilatura import fetch_url, extract
from doc import bitable_insert_record
from lark_util import article_collect_config

os.environ["OPENAI_API_KEY"] = "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"

prompts = {
    "gpt4": {
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
    }
}

re_split = re.compile("。|\n\n|？|！")

client = OpenAI()


def openai_gpt(prompt, temperature=0.7, max_tokens=1280):
    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[{"role": "user", "content": prompt}],
        temperature=temperature,
        max_tokens=max_tokens,
        top_p=1,
        frequency_penalty=0,
        presence_penalty=0,
    )
    return response.choices[0].message.content.strip()


def trans(text: str):
    text = text.strip()
    sentences = re_split.split(text)
    max_token_length = len(text)
    max_para_length = len(text.split("\n\n"))
    piece_count = random.randint(3, 5)
    piece_length = math.ceil(max_token_length / piece_count)
    para_length = math.ceil(max_para_length / piece_count)
    piece_type = "para" if 5 <= max_para_length <= 15 else "sentence"
    titles = ["一", "二", "三", "四", "五", "六"]
    output = []
    output.append(titles.pop(0))
    token_count = 0
    para_count = 0
    token_flag = False
    para_flag = False
    for s in sentences:
        if token_flag:
            output.append(titles.pop(0))
            token_count = 0
            token_flag = False
        if para_flag:
            output.append(titles.pop(0))
            para_count = 0
            para_flag = False
        if s.strip():
            output.append(s.strip() + "。")
            token_count += len(s)
            if token_count >= piece_length and piece_type == "sentence":
                token_flag = True
        else:
            output.append(s)
            para_count += 1
            if para_count >= para_length and piece_type == "para":
                para_flag = True
    output_text = "\n".join(output)
    # output_text = output_text.replace("\n\n", "\n").strip()
    return output_text


def get_url_content(url):
    downloaded = fetch_url(url)
    output = extract(downloaded)
    return output


def gpt_base_process(url):
    origin_content = get_url_content(url)
    title = origin_content.splitlines()[0]

    new_title_prompt = prompts["gpt4"]["step4"].format(title=title)
    new_title = openai_gpt(new_title_prompt)

    article_framework_prompt = prompts["gpt4"]["step1"].format(text=origin_content)
    article_framework = openai_gpt(article_framework_prompt)

    article_prompt = prompts["gpt4"]["step2"].format(text=article_framework)
    article = openai_gpt(article_prompt)

    output = trans(article)

    write_database(
        url, title, new_title, origin_content, output, article_framework, article
    )
    return output


def write_database(
    url, title, new_title, origin_content, output, article_framework, article
):
    app_token = "ZNe3bCaQaaFwZrsrqJXcfOBPnah"
    table_id = "tblhHroNH6EkMCIL"
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
    gpt_base_process("https://mp.weixin.qq.com/s/eOQDZUPyuF4jZdLyePe_MA")
