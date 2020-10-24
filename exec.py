from command import Command


def main():
    """
    コマンドから引数を受け取ってBackLogのAPIを実行

    使用できるコマンド一覧
        get_users
        get_issues
        get_projects
        get_project_issues
        get_project_users

    アウトプットの形式
        csv, json
    """

    command = Command()
    command.exec()


if __name__ == "__main__":
    main()
