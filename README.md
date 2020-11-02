## 何に使うの？
Backlogの情報を手元のファイルに吐き出したいときに使ってね！

## 必要な環境
python >= 3.8
(たぶん3.6以上であれば動く...かも？)

## 環境構築手順
### pythonのインストール
- PCに直接python3.8を入れられるのであればそれでOK

### 既存のpythonが入っていて、バージョンが異なる場合
- pyenv + pipenvがオススメ
  - Macだと[クラスメソッドさんの記事](https://dev.classmethod.jp/articles/environment_to_pipenv-pyenv/)がわかりやすい

- 雑な手順説明
  - pyenvをインストール
  - `pyenv install  3.8.X`でpythonの3.8系をインストール
  - pyenvでインストールされるpythonのディレクトリにPATHを通す
  - `pip install pipenv`でpipenvをインストール


### pipenvが使えるようになったあと...

```
git clone https://github.com/sheep333/backlog_command_py.git

pipenv install
pipenv shell
cp .env.sample .env
## .envに自分のBacklogのSPACE_KEY(サブドメイン)とAPI_KEY(Backlogの個人設定から取得)を.envに記載
```

## コマンドの実行
### コマンドの実行方法

```
python exec.py xxxxx(コマンド名) -p yyyyy(project_id)
```

### 実行できるコマンド一覧
- get_users
  - ユーザ一覧のJSONファイル作成
- get_issues
  - 課題一覧のJSONファイル作成
- get_projects
  - プロジェクト一覧のJSONファイル作成
- get_project_issues(-p必須)
  - プロジェクトの課題一覧のJSONファイル作成
- get_project_users(-p必須)
  - プロジェクトのユーザ一覧のJSONファイル作成
- get_wiki_page_list(-p必須)
  - プロジェクトのWiki一覧のJSONファイル作成
- get_project_data(-p必須)
  - プロジェクトの課題、WikiをHTMLファイルにして出力
