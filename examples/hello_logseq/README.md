# Hello Logseq API
## すること
### 現在のグラフが取得する(間違ったところに追加しないため)

```
data = {"method": "logseq.App.getCurrentGraph", "args": []}
response = request_api(data)
```

### すべてのページの一覧を取り出す。
```
data = {
"method": "logseq.Editor.getAllPages",
"args": []
}
```
一度開いていれば、graph名を指定することもできるが、通常今のグラフのみ

### 指定のページの情報を取り出す。contentが文字
```
data = {
"method": "logseq.Editor.getPageBlocksTree",
"args": [page_name]}
```
ツリー構造になっている。

### 指定のページにblockを追加する。
```
data = {"method": "logseq.Editor.insertBlock", "args": [page_name, block_text]}
```
ページ名がない場合作られる。





## 注意事項
探したが、自動でグラフの切り替えの方法は、わからなかった。