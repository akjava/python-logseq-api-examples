# Linear Issue CSVをLogseq形式へ

イントロだけの記事をNoteに書きました。

このスクリプトは、linearからexportされたissue-csvをLogseq APIを使って、Logseqのページに変換します。

## 引数
実行例
```
python .\linear_to_logseq.py -i "Export Wed Jan 22 2025.csv" -g linear
```
### GraphName
logseqから、新しくグラフを作ってください。
その名前を指定します。
### linear-csv パス
linearからエクスポートしてダウンロードしたcsvのパスを指定してください。

一応サンプルのCSVを用意しています。
```
"ID","Team","Title","Description","Status","Estimate","Priority","Project ID","Project","Creator","Assignee","Labels","Cycle Number","Cycle Name","Cycle Start","Cycle End","Created","Updated","Started","Triaged","Completed","Canceled","Archived","Due Date","Parent issue","Initiatives","Project Milestone ID","Project Milestone","SLA Status","Roadmaps"
"TEAM01","Team","最初",,"Todo",,"No priority","41484bc3-ced8-43a8-b99e-1d05649fd658","MyProject","",,"",,,,,"Mon Jan 13 2025 06:21:52 GMT+0000 (GMT)","Wed Jan 15 2025 13:13:00 GMT+0000 (GMT)",,,,,,,,"","e8069698-8380-4451-a259-f2feabac6aa6","release1",
"TEAM02","Team","つぎ",,"Done",,"No priority","41484bc3-ced8-43a8-b99e-1d05649fd659","MyProject","",,"",,,,,"Mon Jan 13 2025 06:21:53 GMT+0000 (GMT)","Wed Jan 15 2025 13:14:00 GMT+0000 (GMT)","Wed Jan 15 2025 13:23:00 GMT+0000 (GMT)",,"Wed Jan 15 2025 13:33:00 GMT+0000 (GMT)",,,,,"","e8069698-8380-4451-a259-f2feabac6aa6","release1",
"TEAM03","Team","Sub",,"Done",,"No priority","41484bc3-ced8-43a8-b99e-1d05649fd660","MyProject","",,"",,,,,"Mon Jan 13 2025 06:21:54 GMT+0000 (GMT)","Wed Jan 15 2025 13:15:00 GMT+0000 (GMT)",,,,,,,"TEAM02","","e8069698-8380-4451-a259-f2feabac6aa6","release1",
"TEAM04","Team","Sub",,"Done",,"No priority","41484bc3-ced8-43a8-b99e-1d05649fd660","MyProject","",,"",,,,,"Mon Jan 13 2025 06:21:54 GMT+0000 (GMT)","Wed Jan 15 2025 13:15:00 GMT+0000 (GMT)",,,,,,,"TEAM02","","e8069698-8380-4451-a259-f2feabac6aa6","release1",
```
## TODO
続きを書く