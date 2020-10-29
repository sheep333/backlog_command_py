import re

import requests
from pybacklogpy.Issue import (Issue, IssueAttachment, IssueComment,
                               IssueSharedFile)
from pybacklogpy.modules import RequestSender
from pybacklogpy.Project import Project
from pybacklogpy.User import User
from pybacklogpy.Wiki import Wiki, WikiAttachment, WikiSharedFile


class MyRequestSender(RequestSender):

    def __init__(self, config, download_path):
        super().__init__(config)
        self.download_path = download_path

    def get_file(self, path: str, url_param):
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
        filename = get_file_name(response.headers['Content-Disposition'])
        with open(f'{self.download_path}/{filename}', mode='wb') as save_file:
            save_file.write(response.content)
        return f'{self.download_path}/{filename}', response


def changed_init(self, config, download_path='./output/'):
    self.old_init(config)
    self.rs = MyRequestSender(config, download_path)


def apply_patch():
    class_list = [Issue, IssueAttachment, IssueComment, IssueSharedFile, Project, User, Wiki, WikiAttachment, WikiSharedFile]
    for backlog_class in class_list:
        old_init = backlog_class.__init__
        backlog_class.__init__ = changed_init
        backlog_class.old_init = old_init
