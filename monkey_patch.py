import urllib.parse
import re

import requests
from pybacklogpy.Issue import (Issue, IssueAttachment, IssueComment,
                               IssueSharedFile)
from pybacklogpy.modules import RequestSender
from pybacklogpy.Project import Project
from pybacklogpy.User import User
from pybacklogpy.Wiki import Wiki, WikiAttachment
from pybacklogpy.SharedFile import SharedFile


class MyRequestSender(RequestSender):
    """
    ファイルのダウンロード処理のpathを変更できるようにしたパッチクラス
    """
    def __init__(self, config, download_path):
        super().__init__(config)
        self.download_path = download_path

    def get_file(self, path: str, url_param, download_path=None):
        if download_path is None:
            download_path = self.download_path

        def get_file_name(content_disposition_header: str):
            fn = content_disposition_header[
                 content_disposition_header.find('filename') + len('filename'):len(content_disposition_header)]
            m = fn.find('*=')
            fn2 = fn
            if not m == -1:
                fn2 = fn[:m] + fn[m + 2:]
            m = re.search("UTF-8''", fn2)
            if not m:
                return fn2
            return fn2[:m.start()] + fn2[m.end():]

        params = self.payload.copy()
        if url_param:
            for p in url_param:
                params[p] = url_param[p]
        response = requests.get(url=(self.api_url + path), params=params)
        if not response.ok:
            return '', response
        encode_filename = get_file_name(response.headers['Content-Disposition'])
        filename = urllib.parse.unquote(encode_filename)
        with open(f'{download_path}{filename}', mode='wb') as save_file:
            save_file.write(response.content)
        return f'{download_path}{filename}', response


class MySharedFile(SharedFile):
    """
    共有ファイルの取得用パッチ
    """
    def get_file(self, project_id_or_key, shared_file_id, download_path=None):
        path = self.base_path + '/{project_id_or_key}/files/{shared_file_id}'\
            .format(project_id_or_key=project_id_or_key, shared_file_id=shared_file_id)

        return self.rs.get_file(path=path, url_param={}, download_path=download_path)


class MyIssueAttachment(IssueAttachment):
    def get_issue_attachment(self, issue_id_or_key: str, attachment_id: int, download_path=None):
        path = self.base_path + '/{issue_id_or_key}/attachments/{attachment_id}' \
            .format(issue_id_or_key=issue_id_or_key, attachment_id=attachment_id)
        return self.rs.get_file(path, {}, download_path=download_path)


class MyWikiAttachment(WikiAttachment):
    def get_wiki_page_attachment(self, wiki_id, attachment_id=None, download_path=None):
        path = self.base_path + '/{wiki_id}/attachments/{attachment_id}'\
            .format(wiki_id=str(wiki_id), attachment_id=attachment_id)
        return self.rs.get_file(path=path, url_param={}, download_path=download_path)


class MyUser(User):
    """
    ユーザアイコンの取得用パッチ
    """
    def get_user_icon(self, user_id, download_path=None):
        if download_path is None:
            download_path = self.rs.download_path
        path = self.base_path + '/{user_id}/icon'.format(user_id=str(user_id))

        response = self.rs.send_get_request(path=path, url_param={})
        if not response.ok:
            return '', response
        # ユーザーアイコンだけ他と戻り値のパターンが違うので、個別対応
        filename = response.url.split('/')[len(response.url.split('/')) - 1]
        filepath = f'{download_path}{filename}'
        with open(filepath, mode='wb') as save_file:
            save_file.write(response.content)
        return filepath, response


class MyIssue(Issue):
    """
    課題にcountを追加するためのパッチ
    """
    def get_issue_list(self, **kwargs):
        path = self.base_path
        payloads = {}
        list_type_param = [
            'project_id',
            'issue_type_id',
            'category_id',
            'version_id',
            'milestone_id',
            'status_id',
            'priority_id',
            'assignee_id',
            'created_user_id',
            'resolution_id',
            'parent_issue_id',
        ]
        for k, v in kwargs.items():
            if k == 'order' and v not in {'desc', 'asc'}:
                raise ValueError('order は desc または asc のみが使用できます')
            if k == 'count' and not 1 <= v <= 100:
                raise ValueError('count(取得上限)は1-100の範囲で指定してください')
            if k == 'custom_field_text':
                for field_id in v:
                    payloads['customField_{field_id}'.format(field_id=field_id)] = v[field_id]
            if k == 'custom_field_num':
                for field_id in v:
                    if v[field_id]['min']:
                        payloads['customField_{field_id}_min'.format(field_id=field_id)] = v[field_id]['min']
                    if v[field_id]['max']:
                        payloads['customField_{field_id}_max'.format(field_id=field_id)] = v[field_id]['max']
            if k == 'custom_field_date':
                for field_id in v:
                    if v[field_id]['min']:
                        payloads['customField_{field_id}_min'.format(field_id=field_id)] = v[field_id][
                            'min']
                    if v[field_id]['max']:
                        payloads['customField_{field_id}_max'.format(field_id=field_id)] = v[field_id]['max']
            if k == 'custom_field_list':
                for field_id in v:
                    payloads['customField_{field_id}[]'.format(field_id=field_id)] = v[field_id]

            # keyをキャメルケースに変換してバックログのキーと揃える
            backlog_param = re.sub("_(.)", lambda m: m.group(1).upper(), k)
            if k == 'id_':
                backlog_param = ['id[]']
            # リスト型のパラメータの場合はキーに括弧を追加する
            if k in list_type_param:
                backlog_param += '[]'
            payloads[backlog_param] = v

        return self.rs.send_get_request(path=path, url_param=payloads)


def changed_init(self, config, download_path='./output/'):
    self.old_init(config)
    self.rs = MyRequestSender(config, download_path)


def apply_patch():
    """
    各クラスの初期化で読み込んでいるRequestSenderのクラスを変更
    """
    class_list = [Issue, IssueAttachment, IssueComment, IssueSharedFile, Project, MyUser, Wiki, WikiAttachment, MySharedFile]
    for backlog_class in class_list:
        old_init = backlog_class.__init__
        backlog_class.__init__ = changed_init
        backlog_class.old_init = old_init
