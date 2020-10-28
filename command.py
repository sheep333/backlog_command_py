import argparse
import json
import os

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

config = BacklogComConfigure(space_key=SPACE_KEY, api_key=API_KEY)
# TODO: パッチを当てたので、引数にoutput用のディレクトリを追加
issue_api = Issue(config)
issue_attachment_api = IssueAttachment(config)
issue_comment_api = IssueComment(config)
project_api = Project(config)
sharedfile_api = SharedFile(config)
user_api = User(config)
wiki_api = Wiki(config)
wiki_attachment_api = WikiAttachment(config)
wiki_sharedfile_api = WikiSharedFile(config)


class Command:
    def __init__(self):
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
            response = eval(f'self.{self.args.command}')()
            data = self._convert_res_to_dict(response)
            self._create_output_file(data)
        else:
            project, issues, wikis, users, comments = self.get_project_data()
            parse = Parse()

            data = {
                "project": project,
                "issues": issues,
                "wikis": wikis,
                "comments": comments
            }
            parse.create_html_file('issue_list.html', 'issue_list.html', data)
            for issue in issues:
                data["issue"] = issue
                parse.create_html_file('issue_detail.html', f"issue_{issue['id']}.html", data)

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
        response = user_api.get_user_list()
        users = [self._convert_res_to_dict(user) for user in response.content]
        return users

    def get_issues(self):
        response = issue_api.get_issue_list()
        issues = [self._convert_res_to_dict(issue) for issue in response.content]
        return issues

    def get_project(self):
        response = project_api.get_project(project_id_or_key=self.args.project)
        return self._convert_res_to_dict(response)

    def get_projects(self):
        response = project_api.get_project_list()
        projects = [self._convert_res_to_dict(project) for project in response.content]
        return projects

    def get_project_issues(self):
        response = issue_api.get_issue_list(project_id=self.args.project)
        project_issues = [self._convert_res_to_dict(issue) for issue in response.content]
        return project_issues

    def get_project_users(self):
        response = project_api.get_project_user_list(project_id_or_key=self.args.project)
        project_users = [self._convert_res_to_dict(user) for user in response.content]
        return project_users

    def get_issue_comments(self, issue_id):
        response = issue_comment_api.get_comment_list(issue_id_or_key=issue_id)
        comments = [self._convert_res_to_dict(comment) for comment in response]
        return comments

    def get_wiki_page_list(self):
        response = wiki_api.get_wiki_page_list(project_id_or_key=self.args.project)
        wikis = [self._convert_res_to_dict(wiki) for wiki in response.content]
        return wikis

    def get_project_data(self):
        project = self.get_project()
        issues = self.get_project_issues()
        wikis = self.get_wiki_page_list()
        users = self.get_project_users()

        comments = []
        for issue in issues:
            for attachment in issue['attachments']:
                issue_attachment_api.get_issue_attachment(issue_id_or_key=issue['id'], attachment_id=attachment['id'])
            for shared_file in issue['sharedFiles']:
                sharedfile_api.get_file(project_id_or_key=self.args.project, shared_file_id=shared_file['id'])
            comments_res = issue_comment_api.get_comment_list(issue_id_or_key=issue['id'])
            for comment_res in comments_res:
                comments.append(self._convert_res_to_dict(comment_res))

        for wiki in wikis:
            for attachment in wiki['attachments']:
                path = wiki_attachment_api.get_wiki_page_attachment(wiki_id=wiki['id'])
                print(path)
            for shared_file in wiki['sharedFiles']:
                sharedfile_api.get_file(project_id_or_key=self.args.project, shared_file_id=shared_file['id'])

        return project, issues, wikis, users, comments
