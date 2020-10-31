import argparse
import json
import os
import logging

import pandas as pd
from pybacklogpy.BacklogConfigure import BacklogComConfigure
from pybacklogpy.Issue import Issue, IssueAttachment, IssueComment
from pybacklogpy.Project import Project
from pybacklogpy.SharedFile import SharedFile
from pybacklogpy.User import User
from pybacklogpy.Wiki import Wiki, WikiAttachment, WikiSharedFile

from parse import Parse

SPACE_KEY = str(os.getenv('SPACE_KEY'))
API_KEY = os.getenv('API_KEY')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)

config = BacklogComConfigure(space_key=SPACE_KEY, api_key=API_KEY)
# TODO: パッチを当てたので、引数にoutput用のディレクトリを追加


class Command:
    def __init__(self):
        self.issue_api = Issue(config)
        self.issue_attachment_api = IssueAttachment(config)
        self.issue_comment_api = IssueComment(config)
        self.project_api = Project(config)
        self.sharedfile_api = SharedFile(config)
        self.user_api = User(config)
        self.wiki_api = Wiki(config)
        self.wiki_attachment_api = WikiAttachment(config)
        self.wiki_sharedfile_api = WikiSharedFile(config)

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
        parser.add_argument('-u', '--user', type=int, help='ユーザーID')
        parser.add_argument('-p', '--project', help='プロジェクトID')

        parser.add_argument(
            '-o', '--output',
            help='アウトプットの形式',
            default='csv',
            choices=['csv', 'json']
        )

        parser.add_argument(
            '--dir',
            help='データを出力するディレクトリ名',
            default='./output/'
        )

        self.args = parser.parse_args()

    def exec(self):
        if self.args.command != 'get_project_data':
            data = eval(f'self.{self.args.command}')()
            self._create_output_file(data)
        else:
            self.parse = Parse()
            project, issues, wikis, users = self.get_project_data()

            data = {
                "project": project,
                "issues": issues,
                "wikis": wikis
            }
            self.parse.create_html_file('issue_list.html', 'issue_list.html', data)
            for issue in issues:
                data["issue"] = issue
                data["issue"]["description"] = self.parse.to_markdown(issue["description"])
                self.parse.create_html_file('issue_detail.html', f"issue_{issue['id']}.html", data)

    def _create_output_file(self, data):
        if self.args.output == "csv":
            df = pd.DataFrame(data)
            df.to_csv(f"{self.args.dir}{self.args.command}.csv")
        elif self.args.output == "json":
            for index, d in enumerate(data):
                data_file = open(f'{self.args.dir}{self.args.command}_{index}.json', 'w')
                json.dump(data, data_file, ensure_ascii=False, indent=2)

    def _convert_res_to_dict(self, response):
        return json.loads(response.content.decode('utf-8'))

    def get_users(self):
        response = self.user_api.get_user_list()
        return self._convert_res_to_dict(response)

    def get_issues(self):
        response = self.issue_api.get_issue_list()
        return self._convert_res_to_dict(response)

    def get_project(self):
        response = self.project_api.get_project(project_id_or_key=self.args.project)
        return self._convert_res_to_dict(response)

    def get_projects(self):
        response = self.project_api.get_project_list()
        return self._convert_res_to_dict(response)

    def get_project_issues(self):
        response = self.issue_api.get_issue_list(project_id=self.args.project)
        return self._convert_res_to_dict(response)

    def get_project_users(self):
        response = self.project_api.get_project_user_list(project_id_or_key=self.args.project)
        project_users = self._convert_res_to_dict(response)
        return project_users

    def get_issue_comments(self, issue_id):
        response = self.issue_comment_api.get_comment_list(issue_id_or_key=issue_id)
        return self._convert_res_to_dict(response)

    def get_wiki_page_list(self):
        response = self.wiki_api.get_wiki_page_list(project_id_or_key=self.args.project)
        return self._convert_res_to_dict(response)

    def get_project_data(self):
        project = self.get_project()
        issues = self.get_project_issues()
        wikis = self.get_wiki_page_list()
        users = self.get_project_users()

        for issue in issues:
            issue['comments'] = self.get_issue_comments(issue["id"])
            for comment in issue['comments']:
                if "content" in comment and comment["content"] is not None:
                    comment["content"] = self.parse.to_markdown(comment["content"])

            for attachment in issue['attachments']:
                path = self.issue_attachment_api.get_issue_attachment(issue_id_or_key=issue['id'], attachment_id=attachment['id'])
                logger.info(f"Saved issue attachment: {path}")
            for shared_file in issue['sharedFiles']:
                path = self.sharedfile_api.get_file(project_id_or_key=self.args.project, shared_file_id=shared_file['id'])
                logger.info(f"Saved issue sharefile: {path}")

        for wiki in wikis:
            for attachment in wiki['attachments']:
                path = self.wiki_attachment_api.get_wiki_page_attachment(wiki_id=wiki['id'], attachment_id=attachment['id'])
                logger.info(f"Saved wiki attachment: {path}")
            for shared_file in wiki['sharedFiles']:
                path = self.sharedfile_api.get_file(project_id_or_key=self.args.project, shared_file_id=shared_file['id'])
                logger.info(f"Saved wiki sharefile: {path}")

        return project, issues, wikis, users
