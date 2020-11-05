import argparse
import json
import os
import logging
import re

# import pandas as pd
from pybacklogpy.BacklogConfigure import BacklogComConfigure
from pybacklogpy.Issue import Issue, IssueAttachment, IssueComment
from pybacklogpy.Project import Project
from pybacklogpy.Wiki import Wiki, WikiAttachment

from parse import Parse
from monkey_patch import MySharedFile, MyUser

SPACE_KEY = str(os.getenv('SPACE_KEY'))
API_KEY = os.getenv('API_KEY')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

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
            logger.info('Create issue_list.html')
            for issue in issues:
                data['issue'] = issue
                self.parse.create_html_file('issue_detail.html', f'issue_{issue["id"]}.html', data)
                logger.info(f'Create issue_{issue["id"]}.html')
            del data['issues'], data['issue']

            for wiki in wikis:
                data['wiki'] = wiki
                self.parse.create_html_file('wiki.html', f'wiki_{wiki["id"]}.html', data)
                logger.info(f'Create wiki_{wiki["id"]}.html')

    def _init_api(self):
        """
        BacklogのAPIを初期化
        FIXME: output先のディレクトリを変更
        """
        self.issue_api = Issue(config)
        self.issue_attachment_api = IssueAttachment(config)
        self.issue_comment_api = IssueComment(config)
        self.project_api = Project(config)
        self.sharedfile_api = MySharedFile(config)
        self.user_api = MyUser(config)
        self.wiki_api = Wiki(config)
        self.wiki_attachment_api = WikiAttachment(config)

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
        return json.loads(response.content.decode('utf-8'))

    def _add_user_icon(self, obj, users_icon):
        if 'createdUser' in obj:
            obj['createdUser']['icon'] = users_icon[obj['createdUser']['id']]
        if 'updatedUser' in obj:
            obj['updatedUser']['icon'] = users_icon[obj['updatedUser']['id']]
        return

    def _convert_image_link(self, txt):
        """
        テキスト中のimageの記法をimgタグに置換
        """
        filenames = re.findall(r'!\[image\]\[(.*)\]', txt)
        if filenames and txt is not None:
            for filename in filenames:
                file_image = f'<img src="{filename}" class="loom-internal-image">'
                txt = re.sub(r'!\[image\]\[(.*)\]', file_image, txt, 1)
        return txt

    def get_users(self):
        response = self.user_api.get_user_list()
        if response.status_code == 200:
            return self._convert_res_to_dict(response)
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_user_icon(self, user_id):
        filepath, response = self.user_api.get_user_icon(user_id=user_id)
        if response.status_code == 200:
            logger.info(f'Saved user icon: {filepath}')
            return filepath, response
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_issues(self):
        response = self.issue_api.get_issue_list()
        if response.status_code == 200:
            return self._convert_res_to_dict(response)
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_project(self):
        response = self.project_api.get_project(project_id_or_key=self.args.project)
        if response.status_code == 200:
            return self._convert_res_to_dict(response)
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_projects(self):
        response = self.project_api.get_project_list()
        if response.status_code == 200:
            return self._convert_res_to_dict(response)
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_project_icon(self):
        filepath, response = self.project_api.get_project_icon(project_id_or_key=self.args.project)
        if response.status_code == 200:
            logger.info(f'Saved project icon: {filepath}')
            return filepath, response
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_project_issues(self):
        response = self.issue_api.get_issue_list(project_id=self.args.project)
        if response.status_code == 200:
            return self._convert_res_to_dict(response)
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_project_users(self):
        response = self.project_api.get_project_user_list(project_id_or_key=self.args.project)
        if response.status_code == 200:
            project_users = self._convert_res_to_dict(response)
            return project_users
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_issue_comments(self, issue_id):
        response = self.issue_comment_api.get_comment_list(issue_id_or_key=issue_id)
        if response.status_code == 200:
            return self._convert_res_to_dict(response)
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_wiki_page_list(self):
        response = self.wiki_api.get_wiki_page_list(project_id_or_key=self.args.project)
        # 一覧に含まれるWikiにはcontentが含まれないため、改めて取得する
        if response.status_code == 200:
            wikis_list = self._convert_res_to_dict(response)
            return [self._convert_res_to_dict(self.wiki_api.get_wiki_page(wiki['id'])) for wiki in wikis_list]
        else:
            raise EnvironmentError("APIの情報がうまく取得できませんでした...")

    def get_project_data(self):
        """
        APIデータの取得と整形
        """
        project = self.get_project()
        logger.info('Get project data')
        issues = self.get_project_issues()
        logger.info('Get project issues')
        wikis = self.get_wiki_page_list()
        logger.info('Get project wiki')
        users = self.get_project_users()
        logger.info('Get project users')

        # プロジェクトデータにアイコンを追加
        filepath, response = self.get_project_icon()
        # FIXME: /outputの直接変換ではなく引数を判定して置換したい
        project['icon'] = filepath.replace('/output', '')

        # ユーザアイコンの取得用dict作成
        users_icon = {}
        for user in users:
            filepath, response = self.get_user_icon(user['id'])
            # FIXME: /outputの直接変換ではなく引数を判定して置換したい
            users_icon[user['id']] = filepath.replace('/output', '')

        # 課題とそのコメントのアイコン追加、マークダウンへの変換処理、添付ファイル取得
        for issue in issues:
            self._add_user_icon(issue, users_icon)
            description = self._convert_image_link(issue['description'])
            issue['description'] = self.parse.to_markdown(description)

            issue['comments'] = self.get_issue_comments(issue['id'])
            for comment in issue['comments']:
                self._add_user_icon(comment, users_icon)
                content = self._convert_image_link(comment['content'])
                comment['content'] = self.parse.to_markdown(content)
            logger.info('Get comments')

            for attachment in issue['attachments']:
                filepath, response = self.issue_attachment_api.get_issue_attachment(issue_id_or_key=issue['id'], attachment_id=attachment['id'])
                logger.info(f'Saved issue attachment: {filepath}')
            for shared_file in issue['sharedFiles']:
                filepath, response = self.sharedfile_api.get_file(project_id_or_key=self.args.project, shared_file_id=shared_file['id'])
                logger.info(f'Saved issue sharefile: {filepath}')

        # Wikiのマークダウンのアイコン追加、変換処理、添付ファイル取得
        for wiki in wikis:
            self._add_user_icon(wiki, users_icon)
            content = self._convert_image_link(wiki['content'])
            wiki['content'] = self.parse.to_markdown(content)
            for attachment in wiki['attachments']:
                filepath, response = self.wiki_attachment_api.get_wiki_page_attachment(wiki_id=wiki['id'], attachment_id=attachment['id'])
                logger.info(f'Saved wiki attachment: {filepath}')
            for shared_file in wiki['sharedFiles']:
                filepath, response = self.sharedfile_api.get_file(project_id_or_key=self.args.project, shared_file_id=shared_file['id'])
                logger.info(f'Saved wiki sharefile: {filepath}')

        return project, issues, wikis, users
