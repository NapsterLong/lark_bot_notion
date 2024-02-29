import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from lark_oapi.api.docx.v1 import *

from lark_util import doc_manager_config


# https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table/list
def bitable_list_tables(app_token) -> List[AppTable]:
    lark_client = (
        lark.Client.builder()
        .domain(doc_manager_config.domain)
        .app_id(doc_manager_config.app_id)
        .app_secret(doc_manager_config.app_secret)
        .enable_set_token(True)
        .log_level(lark.LogLevel.INFO)
        .build()
    )
    result = []

    # 构造请求对象
    request: ListAppTableRequest = (
        ListAppTableRequest.builder().app_token(app_token).build()
    )

    # 发起请求
    response: ListAppTableResponse = lark_client.bitable.v1.app_table.list(request)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
        )
        return []

    return response.data.items or []


# https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-field/list
def bitable_list_fields(app_token, table_id) -> List[AppTableFieldForList]:
    lark_client = (
        lark.Client.builder()
        .domain(doc_manager_config.domain)
        .app_id(doc_manager_config.app_id)
        .app_secret(doc_manager_config.app_secret)
        .enable_set_token(True)
        .log_level(lark.LogLevel.INFO)
        .build()
    )
    # 构造请求对象
    request: ListAppTableFieldRequest = (
        ListAppTableFieldRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .build()
    )

    # 发起请求
    response: ListAppTableFieldResponse = lark_client.bitable.v1.app_table_field.list(
        request
    )

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table_field.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
        )
        return []

    return response.data.items or []


# https://open.feishu.cn/document/server-docs/docs/bitable-v1/app-table-record/list?appId=cli_a53cc9d5d2f8d013
def bitable_list_records(app_token, table_id) -> List[AppTableRecord]:
    lark_client = (
        lark.Client.builder()
        .domain(doc_manager_config.domain)
        .app_id(doc_manager_config.app_id)
        .app_secret(doc_manager_config.app_secret)
        .enable_set_token(True)
        .log_level(lark.LogLevel.INFO)
        .build()
    )
    # 构造请求对象
    request: ListAppTableRecordRequest = (
        ListAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .build()
    )

    # 发起请求
    response: ListAppTableRecordResponse = lark_client.bitable.v1.app_table_record.list(
        request
    )

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table_record.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
        )
        return []

    return response.data.items or []


def bitable_insert_record(app_token, table_id, record, config=doc_manager_config):
    lark_client = (
        lark.Client.builder()
        .domain(config.domain)
        .app_id(config.app_id)
        .app_secret(config.app_secret)
        .enable_set_token(True)
        .log_level(lark.LogLevel.INFO)
        .build()
    )
    # 构造请求对象
    request: CreateAppTableRecordRequest = (
        CreateAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .request_body(AppTableRecord.builder().fields(record).build())
        .build()
    )

    # 发起请求
    response: CreateAppTableRecordResponse = (
        lark_client.bitable.v1.app_table_record.create(request)
    )

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table_record.create failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
        )
        return False
    else:
        return True


def bitable_delete_record(app_token, table_id, record_id):
    lark_client = (
        lark.Client.builder()
        .domain(doc_manager_config.domain)
        .app_id(doc_manager_config.app_id)
        .app_secret(doc_manager_config.app_secret)
        .enable_set_token(True)
        .log_level(lark.LogLevel.INFO)
        .build()
    )
    # 构造请求对象
    request: DeleteAppTableRecordRequest = (
        DeleteAppTableRecordRequest.builder()
        .app_token(app_token)
        .table_id(table_id)
        .record_id(record_id)
        .build()
    )

    # 发起请求
    response: DeleteAppTableRecordResponse = (
        lark_client.bitable.v1.app_table_record.delete(request)
    )

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.bitable.v1.app_table_record.delete failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
        )
        return False
    else:
        return True


def docx_list_blocks(obj_token) -> List[Block]:
    lark_client = (
        lark.Client.builder()
        .domain(doc_manager_config.domain)
        .app_id(doc_manager_config.app_id)
        .app_secret(doc_manager_config.app_secret)
        .enable_set_token(True)
        .log_level(lark.LogLevel.INFO)
        .build()
    )
    # 构造请求对象
    request: ListDocumentBlockRequest = (
        ListDocumentBlockRequest.builder()
        .document_id(obj_token)
        .page_size(500)
        .document_revision_id(-1)
        .build()
    )

    # 发起请求
    response: ListDocumentBlockResponse = lark_client.docx.v1.document_block.list(
        request
    )

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.docx.v1.document_block.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}"
        )
        return []

    return response.data.items or []
