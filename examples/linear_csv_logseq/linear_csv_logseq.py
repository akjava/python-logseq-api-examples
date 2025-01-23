"""
このスクリプトは、Logseq APIを通じて
Linearのissue-csvとcontentsページ記載された情報(Option)からIssueとProjectに関するページを作ります。

基本 csvは辞書データです。
"""

import argparse
import cProfile
import csv
from datetime import datetime
import json
import os
import pstats
import requests
from tqdm import tqdm

profiling = False
if profiling:
    pr = cProfile.Profile()
    pr.enable()

LOGSEQ_TOKEN = "test_token"  # Replace with your actual token


def parse_arguments():
    """引数を解析します。

    Returns:
    Args
    graph_name - 指定のグラフにだけページを作ります。
    input - csvを指定
    """
    parser = argparse.ArgumentParser(description="create rotated data")
    parser.add_argument("--graph_name", "-g", default="linear", help="Grap hname")
    parser.add_argument("--input", "-i", default="example.csv", help="Input Linear CSV")
    return parser.parse_args()


def convert_date_text(date_text):
    """英語の曜日を日本語に

    Parameters:
    date_text: 英語の曜日

    Returns:
    日本語の曜日
    date_textが空なら空を
    該当しなければ、そのまま返す
    """
    weekdays_en_to_ja = {
        "Mon": "月",
        "Tue": "火",
        "Wed": "水",
        "Thu": "木",
        "Fri": "金",
        "Sat": "土",
        "Sun": "日",
    }

    if not date_text:
        return ""
    date_text = date_text.replace(" (GMT)", "")
    input_datetime = datetime.strptime(date_text, "%a %b %d %Y %H:%M:%S %Z%z")

    jp_text_with_en_weekday = input_datetime.strftime(
        "%Y/%m/%d(%a) %H:%M"
    )  #:%S #秒は不要
    jp_text = jp_text_with_en_weekday
    for en, ja in weekdays_en_to_ja.items():
        jp_text = jp_text_with_en_weekday.replace(en, ja)
        jp_text_with_en_weekday = jp_text  # 次の置換のために更新

    return jp_text


def create_team_priority_status_text(csv):
    """labelを作成

    Parameters:
    csv(dict): csv dict

    Returns:
    置き換えられたtext
    """
    return f"{csv['Team']}/{csv['Priority']}/{csv['Status']}"


def create_milestone_text(csv):
    """labelを作成

    Milestoneは、Projectごとに異なるので、project-milestoneが正しいが、長いのでmilestoneだけ表示する

    Parameters:
    csv(dict): csv dict

    Returns:
    置き換えられたtext
    Milestoneがなければ空のtext
    """
    if csv["Project Milestone"]:
        label = csv["Project Milestone"]
        link = f"{csv['Project']}-{csv['Project Milestone']}"
        return f"[{label}]([[{link}]])"
    else:
        return ""


def csv_to_texts(csv):
    """linear csvからpage blocks-textを作成

    Parameters:
    csv(dict): csv dict

    Returns:
    block-textのarray
    """
    texts = []
    # date label
    ctime_text = convert_date_text(csv["Created"])
    utime_text = convert_date_text(csv["Updated"])
    date_text = f"**作成日** {ctime_text} **更新日** {utime_text}"
    texts.append(date_text)

    # Project Label
    # property version graph is too dirty
    project_text = f"[Project/{csv['Project']}]([[{csv['Project']}]])"
    team_priority_text = create_team_priority_status_text(csv)

    texts.append(f"{project_text} {team_priority_text}")

    label = csv["Labels"]
    label_texts = None
    milestone_text = create_milestone_text(csv)
    if label:
        labels = [f"#{label.strip()}" for label in label.split(",")]
        label_texts = f"{milestone_text} " + " ".join(labels)
    else:
        if milestone_text:  # only add if exist
            label_texts = f"{milestone_text}"  # maybe not start with # possible bug.#rethink about csv_to_text to csv_to_texts
    if label_texts:
        texts.append(label_texts)

    texts += split_block_texts_by_header(csv["Description"])

    if "childrens" in csv:
        texts.append("## 子項目")
        # add as single text
        texts.append(csv["childrens"])

    return texts


def read_csv_with_newlines(filepath):
    """
    改行を含むCSVファイルを読み込む関数

    Parameters:
        filepath (str): CSVファイルのパス

    Returns:
        list: 読み込んだCSVデータをリストのリストで返す
    """
    data = []
    with open(filepath, "r", encoding="utf-8") as file:
        reader = csv.reader(file)
        for row in reader:
            data.append(row)
    return data


def issue_text_to_dict(head, csv_lines):
    """
    issue-csv-textを辞書に変換

    Parameters:
        head (str):header 通常csvの最初の行
        csv_lines:csvテキストのリスト

    Returns:
        list: 読み込んだissue-CSVデータを辞書のリストで返す
    """
    result = []
    for line in csv_lines:
        dict = {}
        for i, key in enumerate(head):
            if i < len(line):
                dict[key] = line[i]
        result.append(dict)
    return result


def count_project(project, project_counter):
    """
    projectに含まれるpageの数を数える

    Parameters:
        project (str):project名
        project_counter (dict):結果を保存するdict

    Returns:
        project_counter (dict): 結果を保存するdict
    """
    if project not in project_counter:
        project_counter[project] = 1
    else:
        project_counter[project] += 1


def uniq_title(title, used_titles):
    """
    titleをユニークなものにする

    同じtitleの場合_{数字} とする
    例 test test testの３つのページが存在すると、test test_1 test_2となる
    Parameters:
        title:元の名前
        used_titles:管理に使うdict

    Returns:
        uniq_name: 元の名前あるいは、数字追加されたユニークな名前
    """
    if title not in used_titles:
        used_titles[title] = 0
        return title
    else:
        index = 1
        while True:
            new_title = f"{title}_{index}"
            if new_title not in used_titles:
                used_titles[new_title] = 0
                # print(f"new title = {new_title}")
                return new_title
            index += 1


def split_block_texts_by_header(text):
    """
    header-textを元に、複数のblocks-textを作成する。
    splitといってもいい？

    Parameters:
        text (str):元のtext

    Returns:
        block_texts (list): # で始まるheaderであろうテキスト (tagも含まれる)
    """
    block_texts = []
    current_texts = []
    lines = text.split("\n")
    for line in lines:
        if line.strip().startswith("#"):
            if current_texts:  # empty is False
                block_texts.append("\n".join(current_texts))
                current_texts.clear()
        current_texts.append(line)

    if current_texts:  # empty is False
        block_texts.append("\n".join(current_texts))
    return block_texts


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

    url = "http://127.0.0.1:12315/api"  # default
    response = requests.post(url, headers=headers, data=json.dumps(data))

    if response.status_code == 200:
        # print(response)
        # print(response.text)
        return response.text
    else:
        print(f"Faild: Status code {response.status_code}")
        print(response.text)


def get_current_graph():
    """
    現在のグラフ名を設定ファイルから取得する
    複数起動時の挙動は不明

    Returns:
        graph-name (str): 選択されている
    """
    data = {"method": "logseq.App.getCurrentGraph", "args": []}
    response = request_api(data)

    return json.loads(response)


def parse_contents(page_tree_blocks):
    """
    Contentsページに書き込まれたProject情報を分割する

    blockのdictからcontent部分のみを抜き出す
    なお、headerが含まれていないと何も返さない

    Parameters:
        page_tree_blocks (list):dictのリスト
    Returns:
        contents-dict (dict): テキストのlistからなる、dictキーはタイトル
    """
    contents = {}
    title = None
    # print(page_tree_blocks)
    for block_dict in page_tree_blocks:
        content = block_dict["content"]
        if content.startswith("# "):
            title = content[2:].strip()
            contents[title] = []
        else:
            if title:
                contents[title].append(content)
            else:
                print("# Header not found yet,skipped")
                print(page_tree_blocks)
    return contents


def convert_history_text(histories):
    """
    履歴リストのリストから、ページに表示するテーブルMarkdownテキストを作成する

    Parameters:
        histories (list):日付,アクション,名前のリストのリスト

    Returns:
        response-text (str): レスポンスのテキスト
    """
    histories = sorted(histories, key=lambda x: x[0])
    texts = []
    texts.append("|日付|アクション|名前|")
    texts.append("|---|---|---|")
    for history in histories:
        texts.append(f"|{'|'.join(history)}|")
    return "\n".join(texts)


def insert_block(page_name, block_text):
    """
    ページにブロックを挿入する。
    ページがなければ、新しく作られる

    Parameters:
        page_name (str):ページ名
        block_text()

    Returns:
        response-text (str): レスポンスのテキスト
    """
    data = {"method": "logseq.Editor.insertBlock", "args": [page_name, block_text]}  #
    return request_api(data)


if __name__ == "__main__":
    used_titles = {}  # uniq_title時に作業用辞書
    project_counter = {}  # projectのpage数を数えるときに使う辞書

    args = parse_arguments()
    current_graph_name = get_current_graph()["name"]
    if current_graph_name != args.graph_name:
        print(
            f"expected graph name is '{args.graph_name}' but current is '{current_graph_name}'"
        )
        exit(0)

    csv_path = args.input
    if not os.path.exists(csv_path):
        print(f"csv not exist {csv_path}")
        exit(0)

    csv_issue_texts = read_csv_with_newlines(csv_path)
    dicts = issue_text_to_dict(
        csv_issue_texts[0], csv_issue_texts[1:]
    )  # first line is header
    # print(dicts[0])

    horizontal = False
    childrens = {}
    project_histories = {}

    for dict in dicts:
        count_project(dict["Project"], project_counter)
        # If same title used change tilte_1,title_2,..
        title = uniq_title(dict["Title"], used_titles)
        dict["Title"] = title

        parent = dict["Parent issue"]
        if parent in childrens:
            childrens[parent].append(f"[[{dict['Title']}]]")
        else:
            childrens[parent] = [f"[[{dict['Title']}]]"]

    action_keys = [
        "Created",
        "Started",
        "Triaged",
        "Completed",
        "Canceled",
        "Archived",
    ]  # update is most of duplicate,I'm not going to check
    for dict in dicts:
        id = dict["ID"]
        if id in childrens:
            if horizontal:
                dict["childrens"] = " ".join(childrens[id])
            else:
                dict["childrens"] = "\n".join(childrens[id])
        # parse histories
        for action_key in action_keys:
            if dict[action_key]:
                history = [
                    convert_date_text(dict[action_key]),
                    action_key,
                    f'{dict["Title"]}',
                ]  # stop sharing title too big link
                if dict["Project"] in project_histories:
                    histories = project_histories[dict["Project"]]
                    histories.append(history)
                else:
                    project_histories[dict["Project"]] = [history]

    print(f"start generating pages at {current_graph_name}")

    # ここでのcontentsとは、logseqの共有ページ:Contentsに記載されたProject情報
    data = {
        "method": "logseq.Editor.getPageBlocksTree",
        "args": ["Contents"],  # Contents are logseq-shared-page
    }
    result = request_api(data)
    contents = parse_contents(json.loads(result))

    # 最初にProjectのページを作成しておく
    for name, count in project_counter.items():
        # initial generate
        """
        example

        # TITLE
        #PROJECT 1項目
        """
        print(f"generate project page {name}")
        project_text = f"#PROJECT {count}項目"
        insert_block(name, project_text)

        if name in contents:
            blocks = contents[name]
            for block in blocks:
                insert_block(name, block)

        # what fuck?
        project_text = convert_history_text(project_histories[name])
        insert_block(name, project_text)

    # Issueごとにページを作成する
    for dict in tqdm(dicts):
        title = dict["Title"]
        print(f"generate {title}")
        block_texts = csv_to_texts(dict)

        for text in block_texts:
            insert_block(title, text)

    # Profile
    if profiling:
        pr.disable()
        s = pstats.Stats(pr)
        # 標準ライブラリのパスを削除
        s.strip_dirs()
        # 累積時間でソートして表示
        s.sort_stats("cumtime").print_stats(10)  # 上位10件を表示
