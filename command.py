import argparse
import json
import os
import pandas as pd

from pybacklogpy.BacklogConfigure import BacklogJpConfigure
from pybacklogpy.Issue import Issue
from pybacklogpy.Project import Project
from pybacklogpy.User import User
from pybacklogpy.Wiki import Wiki

SPACE_KEY = os.getenv('SPACE_KEY')
API_KEY = os.getenv('API_KEY')

config = BacklogJpConfigure(space_key=SPACE_KEY, api_key=API_KEY)
issue_api = Issue(config)
project_api = Project(config)
user_api = User(config)
wiki_api = Wiki(config)


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
        print(self.args.values)

    def exec(self):
        data = eval(self.args.command)(self.args)
        self._create_output_file(data)

    def _create_output_file(self, data):
        if self.args.output == "csv":
            df = pd.DataFrame(data)
            df.to_csv(f"{self.args.dir}{self.args.command}.csv")
        elif self.args.output == "json":
            data_file = open(f'{self.args.dir}{self.args.command}.json', 'w')
            json.dump(data, data_file, indent=2)

    def get_users(self):
        return self.user_api.get_user_list()

    def get_issues(self):
        return self.issue_api.get_issue_list()

    def get_projects(self):
        return self.project_api.get_project_list()

    def get_project_issues(self):
        return self.issue_api.get_issue_list(project_id=self.args.project)

    def get_project_users(self):
        return self.project_api.get_project_user_list(project_id=self.args.project)