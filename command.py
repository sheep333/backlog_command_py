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
        self.issue_api = Issue(config)
        self.issue_attachment_api = IssueAttachment(config)
        self.issue_comment_api = IssueComment(config)
        self.project_api = Project(config)
        self.sharedfile_api = MySharedFile(config)
        self.user_api = MyUser(config)
        self.wiki_api = Wiki(config)
        self.wiki_attachment_api = WikiAttachment(config)

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
            default='json',
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

    def _create_output_file(self, data):
        # if self.args.output == 'csv':
        #    df = pd.DataFrame(data)
        #    df.to_csv(f'{self.args.dir}{self.args.command}.csv')
        if self.args.output == 'json':
            for index, d in enumerate(data):
                data_file = open(f'{self.args.dir}{self.args.command}_{index}.json', 'w')
                json.dump(data, data_file, ensure_ascii=False, indent=2)

    def _convert_res_to_dict(self, response):
        return json.loads(response.content.decode('utf-8'))

    def _add_user_icon(self, obj, users_icon):
        if 'createdUser' in obj:
            obj['createdUser']['icon'] = users_icon[obj['createdUser']['id']]
        if 'updatedUser' in obj:
            obj['updatedUser']['icon'] = users_icon[obj['updatedUser']['id']]
        return

    def _convert_image_link(self, txt):
        if txt is None:
            return txt
        filenames = re.findall(r'!\[image\]\[(.*)\]', txt)
        for filename in filenames:
            file_image = f'<img src="{filename}" class="loom-internal-image">'
            txt = re.sub(r'!\[image\]\[(.*)\]', file_image, txt, 1)
        return txt

    def get_users(self):
        response = self.user_api.get_user_list()
        return self._convert_res_to_dict(response)

    def get_user_icon(self, user_id):
        filepath, response = self.user_api.get_user_icon(user_id=user_id)
        logger.info(f'Saved user icon: {filepath}')
        return filepath, response

    def get_issues(self):
        response = self.issue_api.get_issue_list()
        return self._convert_res_to_dict(response)

    def get_project(self):
        response = self.project_api.get_project(project_id_or_key=self.args.project)
        return self._convert_res_to_dict(response)

    def get_projects(self):
        response = self.project_api.get_project_list()
        return self._convert_res_to_dict(response)

    def get_project_icon(self):
        filepath, response = self.project_api.get_project_icon(project_id_or_key=self.args.project)
        logger.info(f'Saved project icon: {filepath}')
        return filepath, response

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
        wikis_list = self._convert_res_to_dict(response)
        # 一覧に含まれるWikiにはcontentが含まれないため、改めて取得する
        return [self._convert_res_to_dict(self.wiki_api.get_wiki_page(wiki['id'])) for wiki in wikis_list]

    def get_project_data(self):
        project = self.get_project()
        logger.info('Get project data')
        issues = self.get_project_issues()
        logger.info('Get project issues')
        wikis = self.get_wiki_page_list()
        logger.info('Get project wiki')
        users = self.get_project_users()
        logger.info('Get project users')

        filepath, response = self.get_project_icon()
        project['icon'] = filepath.replace('/output', '')

        users_icon = {}
        for user in users:
            filepath, response = self.get_user_icon(user['id'])
            users_icon[user['id']] = filepath.replace('/output', '')

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
