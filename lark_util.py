import json
from collections import namedtuple

import lark_oapi as lark
from lark_oapi.api.auth.v3 import InternalTenantAccessTokenRequest, InternalTenantAccessTokenRequestBody, \
    InternalTenantAccessTokenResponse

BotConfig = namedtuple("BotConfig", ["name", "app_id", "app_secret", "domain", "app_name"])
doc_manager_config = BotConfig("doc_manager", "cli_a53cc9d5d2f8d013", "IHEEn5jcZMK1I6WJLLwXJc6JZVeqxUjc",
                               "https://open.feishu.cn", "文档管理")

lark_client = lark.Client.builder().domain(doc_manager_config.domain).app_id(doc_manager_config.app_id).app_secret(
    doc_manager_config.app_secret).enable_set_token(True).log_level(lark.LogLevel.INFO).build()


def get_tenant_access_token():
    # 构造请求对象
    request: InternalTenantAccessTokenRequest = InternalTenantAccessTokenRequest.builder().request_body(
        InternalTenantAccessTokenRequestBody.builder().app_id(doc_manager_config.app_id).app_secret(
            doc_manager_config.app_secret).build()).build()

    # 发起请求
    response: InternalTenantAccessTokenResponse = lark_client.auth.v3.tenant_access_token.internal(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.auth.v3.tenant_access_token.internal failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    content = json.loads(response.raw.content)
    return content.get("tenant_access_token")
