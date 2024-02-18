from flask import Flask
from flask import request
import logging

app = Flask(__name__)


@app.route("/", methods=["POST"])
def hello_world():
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


def main():
    """
    1. 每天的定时任务，凌晨三点跑；
    2. 遍历整颗wiki树，找到创建时间为昨天的文档，以及Parent的文档
    3. 如果parent文档是bittable类型，插入一条数据
    4. 如果parent文档是docx类型，查看是否存在bitable数据，如果存在，查询token，然后插入数据
    5. 发送bot通知
    :return:
    """
    pass


if __name__ == '__main__':
    app.run("0.0.0.0", 9527, debug=True)
