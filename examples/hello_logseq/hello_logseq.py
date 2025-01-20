"""
このスクリプトは、Logseq APIを通じて
基本のAPIを呼び出すサンプルです。

右サイドバーのContentsにブロックを追加します。
"""

import json

import requests


URL = "http://127.0.0.1:12315/api"
LOGSEQ_TOKEN = "test_token"  # Replace with your actual token


def request_api(data):
    """
    実際にlogseq apiにアクセスして結果を返す

    Parameters:

        data (json):アクセス情報

    Returns:
        response-text (str): レスポンスのテキスト
    """

    headers = {
        "Authorization": f"Bearer {LOGSEQ_TOKEN}",
        "Content-Type": "application/json",
    }

    response = requests.post(URL, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        return response.text
    else:
        print(f"Faild: Status code {response.status_code}")
        print(response.text)


def to_json(response_text):
    """reponse-textをjson形式に"""
    return json.loads(response_text)


if __name__ == "__main__":
    # グラフ名を取り出します
    data = {"method": "logseq.App.getCurrentGraph", "args": []}
    response = request_api(data)
    graph_info = to_json(response)

    print(f"Graph name is '{graph_info['name']}'")

    # すべてのページを取り出します
    data = {"method": "logseq.Editor.getAllPages", "args": []}
    response = request_api(data)
    page_datas = to_json(response)
    print(f"there are {len(page_datas)} pages")
    for page in page_datas:
        print(f"Page name is '{page['name']}'")

    # ページのすべてのブロックを取り出します
    first_name = page_datas[0]["name"]
    data = {
        "method": "logseq.Editor.getPageBlocksTree",
        "args": [first_name],
    }
    response = request_api(data)
    page_blocks_tree = to_json(response)
    print(f"parsed page name is {first_name}")
    for block in page_blocks_tree:
        print(
            f"block content:'{block['content']}' has {len(block['children'])} children"
        )

    # 指定のページにブロックを追加します
    data = {
        "method": "logseq.Editor.insertBlock",
        "args": ["Contents", "Hello logseq api"],
    }
    response = request_api(data)
    block_info = to_json(response)
    print(f"added block_id is '{block_info['uuid']}'")
