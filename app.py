import os
import time

from flask import Flask
from flask import request
from flask_apscheduler import APScheduler

from message import send_msg
from wiki import scan_bitable_node, scan_target_node, get_wiki_node
from doc import *


class Config:
    """App configuration."""

    SCHEDULER_API_ENABLED = True


scheduler = APScheduler()
app = Flask(__name__)
app.config.from_object(Config())


@app.route("/", methods=["GET"])
def index():
    return "Hello World!"


@app.route("/", methods=["POST"])
def lark_callback():
    data = request.json
    print(f"request:{data}")
    rsp = {}
    if "url_verification" == data.get("type", ""):
        challenge = data.get("challenge")
        rsp = {"challenge": challenge}
    else:
        pass
    print(f"response:{rsp}")
    return rsp


def switch_table_id(tables_info):
    for table_info in tables_info:
        if table_info.name in ("全部笔记"):
            return table_info.table_id
    return None


def insert_bitable(c_node, parent_node, app_token, table_id):
    if not table_id:
        tables_info = bitable_list_tables(app_token)
        if not tables_info:
            return
        if len(tables_info) == 1:
            table_id = tables_info[0].table_id
        else:
            table_id = switch_table_id(tables_info)
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
                record = {primary_field.field_name: {
                    "link": f"https://napsterlong.feishu.cn/wiki/{c_node.node_token}", "text": c_node.title}}
                if bitable_insert_record(app_token, table_id, record):
                    content = {"type": "template",
                               "data": {"template_id": "ctp_AA1MTHwpSL1w",
                                        "template_variable":
                                            {"page_title": c_node.title,
                                             "page_url": f"https://napsterlong.feishu.cn/wiki/{c_node.node_token}",
                                             "parent_title": parent_node.title,
                                             "parent_url": f"https://napsterlong.feishu.cn/wiki/{parent_node.node_token}"}}}
                    send_msg("user_id", "4g898ecg", "interactive", content)


@scheduler.task("cron", id="lark_doc2bitable", day="*", hour="03", minute="00", second="00")
def lark_doc2bitable():
    t1 = time.time()
    result_node = scan_target_node()
    for c_node, parent_node in result_node:
        print(c_node.title, c_node.obj_token, parent_node.title, parent_node.obj_token)
        if parent_node.obj_type == "bitable":
            app_token = parent_node.obj_token
            insert_bitable(c_node, parent_node, app_token, None)
        if parent_node.obj_type == "docx":
            app_tokens = []
            for c_block in docx_list_blocks(parent_node.obj_token):
                if c_block.bitable:
                    app_tokens.append(c_block.bitable.token)
            if len(app_tokens) == 1:
                app_token, table_id = app_tokens[0].split("_")
                insert_bitable(c_node, parent_node, app_token, table_id)
    print(f"lark_doc2bitable end,cost:{int(time.time() - t1)}s")


@scheduler.task("cron", id="lark_bitable_auto_delete", day="*", hour="04", minute="00", second="00")
def lark_bitable_auto_delete():
    t1 = time.time()
    result_node = scan_bitable_node()
    for c_node in result_node:
        app_token = c_node.obj_token
        tables_info = bitable_list_tables(app_token)
        if not tables_info:
            return
        if len(tables_info) == 1:
            table_id = tables_info[0].table_id
        else:
            table_id = switch_table_id(tables_info)
        if table_id:
            fields = bitable_list_fields(app_token, table_id)
            primary_field = [f for f in fields if f.is_primary][0]
            if primary_field.ui_type == "Url":
                records = bitable_list_records(app_token, table_id)
                for r in records:
                    primary_value = r.fields.get(primary_field.field_name)
                    primary_value_text = primary_value.get("text")
                    primary_value_link = primary_value.get("link")

                    "https://napsterlong.feishu.cn/wiki/YWW1wixeriqodqkV8Fnc2xa7n6d"
                    url = primary_value_link.split("?")[0]
                    prefix, document_token = os.path.split(url)
                    wiki_node = get_wiki_node(document_token)
                    if not wiki_node:
                        if bitable_delete_record(app_token, table_id, r.record_id):
                            content = {"type": "template",
                                       "data": {"template_id": "ctp_AA1cUMWk9GfI",
                                                "template_variable":
                                                    {"page_title": c_node.title,
                                                     "page_url": f"https://napsterlong.feishu.cn/wiki/{c_node.node_token}",
                                                     "delete_title": primary_value_text}}}
                            send_msg("user_id", "4g898ecg", "interactive", content)
    print(f"lark_bitable_auto_delete end,cost:{int(time.time() - t1)}s")


if __name__ == '__main__':
    lark_bitable_auto_delete()
    # scheduler.init_app(app)
    # scheduler.start()
    # app.run("0.0.0.0", 9527, debug=True, use_reloader=False)
