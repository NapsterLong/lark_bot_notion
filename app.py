import os
import time

from flask import Flask
from flask import request
from flask_apscheduler import APScheduler

from message import send_msg
from wiki import scan_bitable_node, scan_target_node, get_wiki_node
from doc import *
from datetime import datetime


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
    print("lark_doc2bitable start")
    t1 = time.time()
    result_node = scan_target_node()
    add_data = []
    for c_node, parent_node in result_node:
        print(c_node.title, c_node.obj_token, parent_node.title, parent_node.obj_token)
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
                    record = {primary_field.field_name: {
                        "link": f"https://napsterlong.feishu.cn/wiki/{c_node.node_token}", "text": c_node.title}}
                    if bitable_insert_record(app_token, table_id, record):
                        add_data.append({"page_title": c_node.title,
                                         "page_url": f"https://napsterlong.feishu.cn/wiki/{c_node.node_token}",
                                         "database_title": parent_node.title,
                                         "database_url": f"https://napsterlong.feishu.cn/wiki/{parent_node.node_token}"})

    print(f"lark_doc2bitable end,cost:{int(time.time() - t1)}s")
    return add_data


def lark_bitable_auto_delete():
    print("lark_bitable_auto_delete start")
    t1 = time.time()
    result_node = scan_bitable_node()
    delete_data = []
    for c_node in result_node:
        print(c_node.title, c_node.obj_token)
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
                        if bitable_delete_record(app_token, table_id, r.record_id):
                            delete_data.append({"database_title": c_node.title,
                                                "database_url": f"https://napsterlong.feishu.cn/wiki/{c_node.node_token}",
                                                "delete_title": primary_value_text})
    print(f"lark_bitable_auto_delete end,cost:{int(time.time() - t1)}s")
    return delete_data


@scheduler.task("cron", id="lark_doc_job", day="*", hour="03", minute="00", second="00")
def lark_doc_job():
    print("lark_doc_job start")
    add_data = lark_doc2bitable()
    delete_data = lark_bitable_auto_delete()
    today = datetime.today().strftime("%Y-%m-%d")
    content = {"type": "template",
               "data": {"template_id": "ctp_AA1MZVTX3QtW",
                        "template_variable": {
                            "today": today,
                            "add_data": add_data,
                            "delete_data": delete_data
                        }}}
    send_msg("user_id", "4g898ecg", "interactive", content)
    print("lark_doc_job done")


if __name__ == '__main__':
    # lark_doc_job()
    scheduler.init_app(app)
    scheduler.start()
    app.run("0.0.0.0", 9527, debug=True, use_reloader=False)
