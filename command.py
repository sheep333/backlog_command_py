import argparse
import json
import os
import logging
import math
import re

# import pandas as pd
from pybacklogpy.BacklogConfigure import BacklogComConfigure
from pybacklogpy.Issue import Issue, IssueComment
from pybacklogpy.Project import Project
from pybacklogpy.Wiki import Wiki

from parse import Parse
from monkey_patch import MySharedFile, MyUser, MyIssueAttachment, MyWikiAttachment, MyIssue

SPACE_KEY = str(os.getenv('SPACE_KEY'))
API_KEY = os.getenv('API_KEY')
COUNT_PER_API = 2

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)

config = BacklogComConfigure(space_key=SPACE_KEY, api_key=API_KEY)
# TODO: パッチを当てたので、引数にoutput用のディレクトリを追加


class Command:
    def __init__(self):
        self._command_parse()
        self._init_api()
        self.parse = Parse()

    def exec(self):
        if self.args.command != 'get_project_data':
            # get_project_data以外はそのままコマンド名を実行
            data = eval(f'self.{self.args.command}')()
            print(data)
            self.parse.create_output_file(data, self.args)
        else:
            # get_project_dataは各種データをdictで取得
            project, issues, wikis, users = self.get_project_data()

            # 各テンプレートにデータを渡して、それぞれのHTMLファイルを出力
            data = {
                'project': project,
                'issues': issues
            }
            self.parse.create_html_file('issue_list.html', 'issue_list.html', data)
            logger.info('[INFO]Create issue_list.html')
            for issue in issues:
                data['issue'] = issue
                self.parse.create_html_file('issue_detail.html', f'issue_{issue["id"]}.html', data)
                logger.info(f'[INFO]Create issue_{issue["id"]}.html')
            del data['issues'], data['issue']

            for wiki in wikis:
                data['wiki'] = wiki
                self.parse.create_html_file('wiki.html', f'wiki_{wiki["id"]}.html', data)
                logger.info(f'[INFO]Create wiki_{wiki["id"]}.html')

    def _init_api(self):
        """
        BacklogのAPIを初期化
        FIXME: output先のディレクトリを変更
        """
        self.issue_api = MyIssue(config)
        self.issue_attachment_api = MyIssueAttachment(config)
        self.issue_comment_api = IssueComment(config)
        self.project_api = Project(config)
        self.sharedfile_api = MySharedFile(config)
        self.user_api = MyUser(config)
        self.wiki_api = Wiki(config)
        self.wiki_attachment_api = MyWikiAttachment(config)

    def _command_parse(self):
        """
        コマンドラインから受け取った引数をパース
        """
        parser = argparse.ArgumentParser(description='BacklogのAPIをコマンド化したもの')
        parser.add_argument(
            'command',
            help='Backlogの情報に対する操作をおこなう',
            choices=[
                'get_users',
                'get_issues',
                'get_projects',
                'get_project_issues',
                'get_project_users',
                'get_wiki_page_list',
                'get_project_data'
            ]
        )
        parser.add_argument('-p', '--project', help='プロジェクトID')
        parser.add_argument('-u', '--user', type=int, help='ユーザーID')
        parser.add_argument(
            '-o', '--output',
            help='アウトプットの形式',
            default='json',
            choices=['csv', 'json']
        )
        parser.add_argument(
            '--dir',
            help='データを出力するディレクトリ名',
            default='./output/'
        )
        self.args = parser.parse_args()

    def _convert_res_to_dict(self, response):
        """
        レスポンスから必要なデータを取得しをdict型に変換
        """
        logger.debug(f"[DEBUG]Response:{response.content}")
        try:
            return json.loads(response.content.decode('utf-8', errors='replace'))
        except Exception:
            logger.error("[ERROR]レスポンスがデコードできないため、スキップします。")

    def _add_user_icon(self, obj, users_icon):
        if 'createdUser' in obj and obj['createdUser']['id'] in users_icon:
            obj['createdUser']['icon'] = users_icon[obj['createdUser']['id']]
        if 'updatedUser' in obj and obj['updatedUser']['id'] in users_icon:
            obj['updatedUser']['icon'] = users_icon[obj['updatedUser']['id']]
        return

    def _convert_image_link(self, txt, path):
        """
        テキスト中のimageの記法をimgタグに置換
        """
        if txt is not None:
            # FIXME:re.subだけで置換できるような気もする...
            filenames = re.findall(r'!\[image\]\[(.*)\]', txt)
            if filenames:
                for filename in filenames:
                    file_image = f'<img src="../{path}{filename}" class="loom-internal-image">'
                    txt = re.sub(r'!\[image\]\[(.*)\]', file_image, txt, 1)
        return txt

    def _check_status(self, response):
        res = self._convert_res_to_dict(response)
        if response.status_code == 200:
            return res
        else:
            logger.error(res)
            raise EnvironmentError("[ERROR]APIの情報がうまく取得できませんでした...")

    def get_users(self):
        response = self.user_api.get_user_list()
        return self._check_status(response)

    def get_user_icon(self, user_id, download_path=None):
        filepath, response = self.user_api.get_user_icon(user_id=user_id, download_path=download_path)
        logger.info(f'[INFO]Saved user icon: {filepath}')
        if response.status_code == 200:
            return filepath, response
        else:
            logger.warning(f"[WARNING]ユーザID: {user_id}のアイコンが取得できませんでした。")

    def get_issues(self):
        response = self.issue_api.get_issue_list()
        return self._check_status(response)

    def get_project(self):
        response = self.project_api.get_project(project_id_or_key=self.args.project)
        return self._check_status(response)

    def get_projects(self):
        response = self.project_api.get_project_list()
        return self._check_status(response)

    def get_project_icon(self):
        filepath, response = self.project_api.get_project_icon(project_id_or_key=self.args.project)
        logger.info(f'[INFO]Saved project icon: {filepath}')
        if response.status_code == 200:
            return filepath, response
        else:
            logger.warning(f"[WARNING]プロジェクトID: {self.args.project}のアイコンが取得できませんでした。")

    def get_project_issues(self):
        count_response = self.issue_api.count_issue(
            project_id=self.args.project
        )
        count_res = self._check_status(count_response)
        file_count = math.ceil(count_res["count"] / COUNT_PER_API)

        issues = []
        for i in range(file_count):
            response = self.issue_api.get_issue_list(
                project_id=self.args.project,
                count=COUNT_PER_API,
                offset=i * COUNT_PER_API
            )
            res = self._check_status(response)
            issues += res
        return issues

    def get_project_users(self):
        response = self.project_api.get_project_user_list(project_id_or_key=self.args.project)
        return self._check_status(response)

    def get_issue_comments(self, issue_id):
        response = self.issue_comment_api.get_comment_list(
            issue_id_or_key=issue_id,
            count=COUNT_PER_API,
        )
        return self._check_status(response)

    def get_wiki_page_list(self):
        response = self.wiki_api.get_wiki_page_list(project_id_or_key=self.args.project)
        # 一覧に含まれるWikiにはcontentが含まれないため、改めて取得する
        wikis_list = self._check_status(response)
        return [self._convert_res_to_dict(self.wiki_api.get_wiki_page(wiki['id'])) for wiki in wikis_list]

    def _add_file(self, func, data, data_type, **kwargs):
        try:
            logger.debug(f"[DEBUG]{data_type} ID: {data['id']}の処理を開始")
            filepath, response = func(**kwargs)
            logger.info(f'[INFO]Saved {data_type}({data["id"]}): {filepath}')
            data['path'] = filepath
        except Exception as e:
            logger.error(f"{data_type} ID:{data['id']}が取得できませんでした。エラーメッセージ:{e}")

    def create_issue_template_data(self, issues, users_icon):
        # 課題とそのコメントのアイコン追加、マークダウンへの変換処理、添付ファイル取得
        for issue in issues:
            logger.debug(f"[DEBUG]課題ID: {issue['id']}の処理を開始")
            self._add_user_icon(issue, users_icon)

            path = f"./output/issues/{issue['id']}/"
            os.makedirs(path, exist_ok=True)

            description = self._convert_image_link(issue['description'], path)
            issue['description'] = self.parse.to_markdown(description)

            issue['comments'] = self.get_issue_comments(issue['id'])
            for comment in issue['comments']:
                logger.debug(f"[DEBUG]コメントID: {comment['id']}の処理を開始")
                self._add_user_icon(comment, users_icon)
                content = self._convert_image_link(comment['content'], path)
                comment['content'] = self.parse.to_markdown(content)
            logger.info(f'[INFO]Get comments of issue. IssueID: {issue["id"]}')

            for attachment in issue['attachments']:
                param = {
                    "issue_id_or_key": issue['id'],
                    "attachment_id": attachment['id'],
                    "download_path": path
                }
                self._add_file(self.issue_attachment_api.get_issue_attachment, attachment, 'issue_attachment', **param)

            for shared_file in issue['sharedFiles']:
                param = {
                    "project_id_or_key": self.args.project,
                    "shared_file_id": shared_file['id'],
                    "download_path": path
                }
                self._add_file(self.sharedfile_api.get_file, shared_file, 'issue_shared_file', **param)
        return issues

    def create_wiki_template_data(self, wikis, users_icon):
        # Wikiのマークダウンのアイコン追加、変換処理、添付ファイル取得
        for wiki in wikis:
            logger.debug(f"[DEBUG]WikiID: {wiki['id']}の処理を開始")
            self._add_user_icon(wiki, users_icon)

            path = f"./output/wikis/{wiki['id']}/"
            os.makedirs(path, exist_ok=True)

            content = self._convert_image_link(wiki['content'], path)
            wiki['content'] = self.parse.to_markdown(content)

            for attachment in wiki['attachments']:
                param = {
                    "wiki_id": wiki['id'],
                    "attachment_id": attachment['id'],
                    "download_path": path
                }
                self._add_file(self.wiki_attachment_api.get_wiki_page_attachment, attachment, 'wiki_attachment', **param)

            for shared_file in wiki['sharedFiles']:
                param = {
                    "project_id_or_key": self.args.project,
                    "shared_file_id": shared_file['id'],
                    "download_path": path
                }
                self._add_file(self.sharedfile_api.get_file, shared_file, 'wiki_shared_file', **param)
        return wikis

    def get_project_data(self):
        """
        APIデータの取得と整形
        """
        if not SPACE_KEY or not API_KEY:
            raise AttributeError("スペース情報かAPI KEYが取得できませんでした。")

        if not self.args.project:
            raise AttributeError("プロジェクトIDを引数に指定してください。")

        project = self.get_project()
        logger.info('[INFO]Get project data')
        issues = self.get_project_issues()
        logger.info('[INFO]Get project issues')
        wikis = self.get_wiki_page_list()
        logger.info('[INFO]Get project wiki')
        users = self.get_project_users()
        logger.info('[INFO]Get project users')

        # プロジェクトデータにアイコンを追加
        filepath, response = self.get_project_icon()
        # FIXME: /outputの直接変換ではなく引数を判定して置換したい
        project['icon'] = filepath.replace('/output', '')

        # ユーザアイコンの取得用dict作成
        users_icon = {}
        for user in users:
            logger.debug(f"[DEBUG]ユーザID: {user['id']} の処理を開始")
            path = f"./output/users/{user['id']}/"
            os.makedirs(path, exist_ok=True)
            try:
                filepath, response = self.get_user_icon(user['id'], download_path=path)
                users_icon[user['id']] = filepath
            except Exception as e:
                logger.warning(f"[WARNING]ユーザID:{user['id']}のユーザアイコンが取得できませんでした。エラーメッセージ:{e}")

        issues = self.create_issue_template_data(issues, users_icon)
        wikis = self.create_wiki_template_data(wikis, users_icon)

        return project, issues, wikis, users
