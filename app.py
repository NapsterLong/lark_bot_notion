from flask import Flask
from flask import request


app = Flask(__name__)


@app.route("/", methods=["POST"])
def hello_world():
    data = request.json
    rsp = {}
    if "url_verification" == data.get("type", ""):
        challenge = data.get("challenge")
        rsp = {"challenge": challenge}
    else:
        pass
    return rsp
