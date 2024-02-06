from flask import Flask
from flask import request
import logging

app = Flask(__name__)


@app.route("/", methods=["POST"])
def hello_world():
    data = request.json
    logging.info(f"request:{data}")
    rsp = {}
    if "url_verification" == data.get("type", ""):
        challenge = data.get("challenge")
        rsp = {"challenge": challenge}
    else:
        pass
    logging.info(f"response:{rsp}")
    return rsp
