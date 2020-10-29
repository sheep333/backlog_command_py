from jinja2 import Environment, FileSystemLoader


class Parse:

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
