from jinja2 import Environment, FileSystemLoader, Markup
import json
from markdown import markdown


class Parse:
    """
    受け取ったデータをファイルとして作成するクラス
    """

    def create_html_file(self, template_name, file_name, data, output_path="./output/"):
        """
        Jinja2のテンプレートエンジンを使って、HTMLファイルを作成する
        """
        env = Environment(loader=FileSystemLoader('./templates/'))
        template = env.get_template(template_name)
        output_html = template.render(data)
        html_file = open(f"{output_path}{file_name}", "w", encoding="utf-8")
        html_file.write(output_html)
        html_file.close()

    def to_markdown(self, data):
        """
        テキストデータのマークアップへの変換処理
        """
        if data is None:
            data = ''

        return Markup(markdown(data, extensions=['fenced_code']))

    def create_output_file(self, data, args):
        """
        各種ファイルの出力
        """
        # if self.args.output == 'csv':
        #    df = pd.DataFrame(data)
        #    df.to_csv(f'{self.args.dir}{self.args.command}.csv')
        if args.output == 'json':
            for index, d in enumerate(data):
                data_file = open(f'{args.dir}{args.command}_{index}.json', 'w')
                json.dump(data, data_file, ensure_ascii=False, indent=2)
