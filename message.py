import json

import lark_oapi as lark
from lark_oapi.api.im.v1 import *

from lark_util import doc_manager_config


def send_msg(receive_id_type, receive_id, msg_type, content):
    lark_client = lark.Client.builder().domain(doc_manager_config.domain).app_id(doc_manager_config.app_id).app_secret(
        doc_manager_config.app_secret).enable_set_token(True).log_level(lark.LogLevel.INFO).build()
    # 构造请求对象
    request: CreateMessageRequest = CreateMessageRequest.builder().receive_id_type(receive_id_type).request_body(
        CreateMessageRequestBody.builder().receive_id(receive_id).msg_type(msg_type).content(
            json.dumps(content)).build()).build()
    # 发起请求
    response: CreateMessageResponse = lark_client.im.v1.message.create(request)
    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.im.v1.message.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return False
    # 处理业务结果
    return True
