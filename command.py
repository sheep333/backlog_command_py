import argparse
import json
import os
import pandas as pd

from pybacklogpy.BacklogConfigure import BacklogComConfigure
from pybacklogpy.Issue import Issue, IssueAttachment, IssueComment, IssueSharedFile
from pybacklogpy.Project import Project
from pybacklogpy.User import User
from pybacklogpy.Wiki import Wiki, WikiAttachment, WikiSharedFile

SPACE_KEY = str(os.getenv('SPACE_KEY'))
API_KEY = os.getenv('API_KEY')

config = BacklogComConfigure(space_key=SPACE_KEY, api_key=API_KEY)
# TODO: パッチを当てたので、引数にoutput用のディレクトリを追加
issue_api = Issue(config)
issue_attachment_api = IssueAttachment(config)
issue_comment_api = IssueComment(config)
issue_sharedfile_api = IssueSharedFile(config)
project_api = Project(config)
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
                'get_issue_comments',
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
            data = json.loads(response.content.decode('utf-8'))
            self._create_output_file(data)
        # else:
        # TODO: それぞれを結び付けてJSONにするかdictにしてテンプレートを作成するか何かする

    def _create_output_file(self, data):
        if self.args.output == "csv":
            df = pd.DataFrame(data)
            df.to_csv(f"{self.args.dir}{self.args.command}.csv")
        elif self.args.output == "json":
            for index, d in enumerate(data):
                data_file = open(f'{self.args.dir}{self.args.command}_{index}.json', 'w')
                json.dump(data, data_file, ensure_ascii=False, indent=2)

    def get_users(self):
        return user_api.get_user_list()

    def get_issues(self):
        return issue_api.get_issue_list()

    def get_projects(self):
        return project_api.get_project_list()

    def get_project_issues(self):
        return issue_api.get_issue_list(project_id=self.args.project)

    def get_project_users(self):
        return project_api.get_project_user_list(project_id=self.args.project)

    def get_issue_comments(self):
        return issue_comment_api.get_comment_list(issue_id_or_key=8810734)

    def get_wiki_page_list(self):
        return wiki_api.get_wiki_page_list(project_id_or_key=self.args.project)

    def get_project_data(self):
        issues = issue_api.get_issue_list(project_id=self.args.project)
        wikis = wiki_api.get_wiki_page_list(project_id=self.args.project)
        users = project_api.get_project_user_list(project_id=self.args.project)

        comments = []
        for issue in issues:
            issue_attachment_api.get_list_of_issue_attachments(issue_id_or_key=issue['id'])
            issue_sharedfile_api.get_list_of_linked_shared_files(issue_id_or_key=issue['id'])
            comment = issue_comment_api.get_comment_list(issue_id_or_key=issue['id'])
            comments.append(comment)

        for wiki in wikis:
            wiki_attachment_api.get_list_of_wiki_attachments(wiki_id=wiki['id'])
            wiki_sharedfile_api.get_list_of_shared_files_on_wiki(wiki_id=wiki['id'])

        return issues, wikis, users, comments
