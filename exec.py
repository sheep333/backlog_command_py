from command import Command
from monkey_patch import apply_patch


def main():
    """
    コマンドから引数を受け取ってBackLogのAPIを実行

    使用できるコマンド一覧
        get_users
        get_issues
        get_projects
        get_project_issues
        get_project_users
        get_issue_comments
        get_wiki_page_list

    アウトプットの形式
        csv, json
    """
    # apply_patch()
    command = Command()
    command.exec()


if __name__ == "__main__":
    main()
