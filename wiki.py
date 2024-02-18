import json
import os
from collections import namedtuple

import lark_oapi as lark
from lark_oapi.api.auth.v3 import InternalTenantAccessTokenRequest, InternalTenantAccessTokenRequestBody, \
    InternalTenantAccessTokenResponse
from lark_oapi.api.wiki.v2 import *

BotConfig = namedtuple("BotConfig", ["name", "app_id", "app_secret", "domain", "app_name"])
doc_manager_config = BotConfig("doc_manager", "cli_a53cc9d5d2f8d013", "IHEEn5jcZMK1I6WJLLwXJc6JZVeqxUjc",
                               "https://open.feishu.cn", "文档管理")
space_id = "7306385583323185153"


def get_tenant_access_token():
    client = lark.Client.builder().domain(doc_manager_config.domain).app_id(doc_manager_config.app_id).app_secret(
        doc_manager_config.app_secret).enable_set_token(True).log_level(lark.LogLevel.INFO).build()
    # 构造请求对象
    request: InternalTenantAccessTokenRequest = InternalTenantAccessTokenRequest.builder().request_body(
        InternalTenantAccessTokenRequestBody.builder().app_id(doc_manager_config.app_id).app_secret(
            doc_manager_config.app_secret).build()).build()

    # 发起请求
    response: InternalTenantAccessTokenResponse = client.auth.v3.tenant_access_token.internal(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.auth.v3.tenant_access_token.internal failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    content = json.loads(response.raw.content)
    return content.get("tenant_access_token")


def nodes(page_token=None, parent_node_token=None) -> ListSpaceNodeResponseBody:
    # 创建client
    # 使用 user_access_token 需开启 token 配置, 并在 request_option 中配置 token
    client = lark.Client.builder().enable_set_token(True).log_level(lark.LogLevel.DEBUG).build()

    # 构造请求对象
    builder = ListSpaceNodeRequest.builder().space_id(space_id).page_size(50)
    if page_token:
        builder = builder.page_token(page_token)
    if parent_node_token:
        builder = builder.parent_node_token(parent_node_token)
    request: ListSpaceNodeRequest = builder.build()

    # 发起请求
    option = lark.RequestOption.builder().user_access_token(get_tenant_access_token()).build()
    response: ListSpaceNodeResponse = client.wiki.v2.space_node.list(request, option)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.wiki.v2.space_node.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    # 处理业务结果
    lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return response.data


if __name__ == '__main__':
    nodes(parent_node_token="BNRWw849ri9za4kPXiKc3uIPnse")
