import os
import random
import sys

sys.path.append(os.path.dirname(__file__))
import time
import json
from logging.config import dictConfig
from flask import Flask
from flask import request
from flask_apscheduler import APScheduler
from concurrent.futures import ThreadPoolExecutor
from message import send_msg, reply_msg
from wiki import scan_bitable_node, scan_target_node, get_wiki_node
from doc import *
from datetime import datetime
from util import is_url
from lark_util import doc_manager_config, article_collect_config
from article.auto_cw import get_related_article_depth, get_article_read_num, auto_collect, auto_cw
from article.auto_gc import auto_gc_process, all_exist_articles

dictConfig(
    {
        "version": 1,
        "formatters": {
            "default": {
                "format": "[%(asctime)s] %(levelname)s in %(module)s: %(message)s",
            }
        },
        "handlers": {
            "wsgi": {
                "class": "logging.StreamHandler",
                "stream": "ext://flask.logging.wsgi_errors_stream",
                "formatter": "default",
            }
        },
        "root": {"level": "INFO", "handlers": ["wsgi"]},
    }
)

executors = ThreadPoolExecutor(8)


class Config:
    """App configuration."""

    SCHEDULER_API_ENABLED = True


scheduler = APScheduler()
app = Flask(__name__)
app.config.from_object(Config())
logger = app.logger


@app.route("/", methods=["GET"])
def index():
    return "Hello World!"


@app.route("/", methods=["POST"])
def lark_callback():
    data = request.json
    logger.info(f"request:{data}")
    rsp = {}
    if "url_verification" == data.get("type", ""):
        challenge = data.get("challenge")
        rsp = {"challenge": challenge}
    else:
        pass
    logger.info(f"response:{rsp}")
    return rsp


@app.route("/article", methods=["POST"])
def article_callback():
    data = request.json
    logger.info(f"request:{data}")
    header = data.get("header", {})
    event = data.get("event", {})
    rsp = {}
    if "url_verification" == data.get("type", ""):
        challenge = data.get("challenge")
        rsp = {"challenge": challenge}
    elif header.get("event_type") == "im.message.receive_v1":
        message = event.get("message", {})
        message_id = message.get("message_id")
        sender = event.get("sender", {})
        open_id = sender.get("sender_id", {}).get("open_id")
        if message.get("message_type") == "text":
            content = message.get("content")
            text = json.loads(content).get("text")
            if str(text).startswith("/auto"):
                reply_msg({"text": "素材自动收集中，请稍等。"}, "text", message_id, article_collect_config)
                if str(text).startswith("/autowechat"):
                    cookie = text[len("/autowechat"):].strip()
                    executors.submit(auto_cw, cookie, message_id, "wechat")
                else:
                    cookie = text[len("/auto"):].strip()
                    executors.submit(auto_collect, cookie, message_id)
            elif is_url(text):
                reply_msg({"text": "素材处理中，请稍等。"}, "text", message_id, article_collect_config)
                executors.submit(auto_gc_process, text, message_id)
            else:
                reply_msg({"text": "对不起，输入有误！"}, "text", message_id, article_collect_config)
    logger.info(f"response:{rsp}")
    return rsp


def switch_table_id(tables_info):
    for table_info in tables_info:
        if table_info.name in ("全部笔记"):
            return table_info.table_id
    return None


def get_app_token_and_table_id_from_node(c_node):
    app_token = None
    table_id = None
    if c_node.obj_type == "bitable":
        app_token = c_node.obj_token
        tables_info = bitable_list_tables(app_token)
        if len(tables_info) == 1:
            table_id = tables_info[0].table_id
        else:
            table_id = switch_table_id(tables_info)
    if c_node.obj_type == "docx":
        app_tokens = []
        for c_block in docx_list_blocks(c_node.obj_token):
            if c_block.bitable:
                app_tokens.append(c_block.bitable.token)
        if len(app_tokens) == 1:
            app_token, table_id = app_tokens[0].split("_")
    return app_token, table_id


def lark_doc2bitable():
    logger.info("lark_doc2bitable start")
    t1 = time.time()
    result_node = scan_target_node()
    add_data = []
    for c_node, parent_node in result_node:
        # logger.info(c_node.title, c_node.obj_token, parent_node.title, parent_node.obj_token)
        app_token, table_id = get_app_token_and_table_id_from_node(parent_node)
        if table_id:
            fields = bitable_list_fields(app_token, table_id)
            primary_field = [f for f in fields if f.is_primary][0]
            if primary_field.ui_type == "Url":
                records = bitable_list_records(app_token, table_id)
                flag = False
                for r in records:
                    primary_value = r.fields.get(primary_field.field_name)
                    primary_value_link = primary_value.get("link")
                    # 如果当前文档的node token出现在记录当中，说明数据已经写入
                    if c_node.node_token in primary_value_link:
                        flag = True
                if not flag:
                    record = {
                        primary_field.field_name: {
                            "link": f"https://napsterlong.feishu.cn/wiki/{c_node.node_token}",
                            "text": c_node.title,
                        }
                    }
                    logger.info(f"add,{parent_node.title},{c_node.title}")
                    if bitable_insert_record(app_token, table_id, record):
                        add_data.append(
                            {
                                "page_title": c_node.title,
                                "page_url": f"https://napsterlong.feishu.cn/wiki/{c_node.node_token}",
                                "database_title": parent_node.title,
                                "database_url": f"https://napsterlong.feishu.cn/wiki/{parent_node.node_token}",
                            }
                        )

    logger.info(f"lark_doc2bitable end,cost:{int(time.time() - t1)}s")
    return add_data


def lark_bitable_auto_delete():
    logger.info("lark_bitable_auto_delete start")
    t1 = time.time()
    result_node = scan_bitable_node()
    delete_data = []
    for c_node in result_node:
        # logger.info(c_node.title, c_node.obj_token)
        app_token, table_id = get_app_token_and_table_id_from_node(c_node)
        if table_id:
            fields = bitable_list_fields(app_token, table_id)
            primary_field = [f for f in fields if f.is_primary][0]
            if primary_field.ui_type == "Url":
                records = bitable_list_records(app_token, table_id)
                for r in records:
                    primary_value = r.fields.get(primary_field.field_name)
                    primary_value_text = primary_value.get("text")
                    primary_value_link = primary_value.get("link")
                    url = primary_value_link.split("?")[0]
                    prefix, document_token = os.path.split(url)
                    wiki_node = get_wiki_node(document_token)
                    if not wiki_node:
                        logger.info(f"delete,{c_node.title},{primary_value_text}")
                        if bitable_delete_record(app_token, table_id, r.record_id):
                            delete_data.append(
                                {
                                    "database_title": c_node.title,
                                    "database_url": f"https://napsterlong.feishu.cn/wiki/{c_node.node_token}",
                                    "delete_title": primary_value_text,
                                }
                            )
    logger.info(f"lark_bitable_auto_delete end,cost:{int(time.time() - t1)}s")
    return delete_data


@scheduler.task("cron", id="lark_doc_job", day="*", hour="3", minute="00", second="00")
def lark_doc_job():
    logger.info("lark_doc_job start")
    add_data = lark_doc2bitable()
    delete_data = lark_bitable_auto_delete()
    today = datetime.today().strftime("%Y-%m-%d")
    content = {
        "type": "template",
        "data": {
            "template_id": "ctp_AA1MZVTX3QtW",
            "template_variable": {
                "today": today,
                "add_data": add_data,
                "delete_data": delete_data,
            },
        },
    }
    send_msg("user_id", "4g898ecg", "interactive", content)
    logger.info("lark_doc_job done")


if __name__ == "__main__":
    scheduler.init_app(app)
    scheduler.start()
    app.run("0.0.0.0", 9527, debug=True, use_reloader=False)
