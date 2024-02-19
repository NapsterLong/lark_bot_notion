from datetime import datetime, timedelta
import lark_oapi as lark
from lark_oapi.api.wiki.v2 import *

from lark_util import lark_client

space_id = "7306385583323185153"


def get_wiki_node(wiki_token) -> Optional[Node]:
    # 构造请求对象
    request: GetNodeSpaceRequest = GetNodeSpaceRequest.builder().token(wiki_token).build()

    # 发起请求
    option = lark.RequestOption.builder().build()
    response: GetNodeSpaceResponse = lark_client.wiki.v2.space.get_node(request, option)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.wiki.v2.space.get_node failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    return response.data.node


def nodes(page_token=None, parent_node_token=None) -> Optional[ListSpaceNodeResponseBody]:
    # 构造请求对象
    builder = ListSpaceNodeRequest.builder().space_id(space_id).page_size(50)
    if page_token:
        builder = builder.page_token(page_token)
    if parent_node_token:
        builder = builder.parent_node_token(parent_node_token)
    request: ListSpaceNodeRequest = builder.build()

    # 发起请求
    option = lark.RequestOption.builder().build()
    response: ListSpaceNodeResponse = lark_client.wiki.v2.space_node.list(request, option)

    # 处理失败返回
    if not response.success():
        lark.logger.error(
            f"client.wiki.v2.space_node.list failed, code: {response.code}, msg: {response.msg}, log_id: {response.get_log_id()}")
        return

    # 处理业务结果
    # lark.logger.info(lark.JSON.marshal(response.data, indent=4))
    return response.data


def nodes_all(parent_node_token=None) -> List[Node]:
    result = []
    last_node = nodes(None, parent_node_token)
    if last_node.items:
        result.extend(last_node.items)
    flag = last_node.has_more
    while flag:
        new_node = nodes(last_node.page_token, parent_node_token)
        if new_node.items:
            result.extend(new_node.items)
        flag = new_node.has_more
    return result


today = datetime.today()
last_7 = today - timedelta(days=60)
start_ts = int(last_7.timestamp())
end_ts = int(today.timestamp())


def scan_target_node(parent_node_token=None, parent_node: Node = None):
    result = []
    for c_node in nodes_all(parent_node_token):
        if parent_node:
            if start_ts <= int(c_node.node_create_time) <= end_ts and parent_node.obj_type in ("docx", "bitable"):
                result.append((c_node, parent_node))
        result.extend(scan_target_node(c_node.node_token, c_node))
    return result


def scan_bitable_node(parent_node_token=None):
    result = []
    for c_node in nodes_all(parent_node_token):
        if c_node.obj_type == "bitable":
            result.append(c_node)
        if start_ts <= int(c_node.obj_edit_time) <= end_ts and c_node.obj_type == "docx":
            result.append(c_node)
        result.extend(scan_bitable_node(c_node.node_token))
    return result


if __name__ == '__main__':
    print(get_wiki_node("VC2EwGqWfijEamkPH9ecuswAn6c").title)
