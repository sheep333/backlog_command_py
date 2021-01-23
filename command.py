import argparse
import logging

from parse import Parse
from backlog import Backlog

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.INFO)


class Command:
    def __init__(self):
        self._command_parse()
        self.parse = Parse()
        self.backlog = Backlog(self.args.project)

    def exec(self):
        logger.debug(f"[DEBUG]コマンド: {self.args.command}がコールされました。")
        if self.args.command != 'get_project_data':
            # get_project_data以外はそのままコマンド名を実行
            data = eval(f'self.backlog.{self.args.command}()')
            self.parse.create_output_file(data, self.args)
        else:
            # TODO:あとでBacklogクラスに移行
            # get_project_dataは各種データをdictで取得
            project, issues, wikis, users = self.backlog.get_project_data()

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
