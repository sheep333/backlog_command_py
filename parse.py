from jinja2 import Template


class Parse:

    def to_html(self, template_name, file_name, output_path, data):
        """
        dict型のデータを
        """
        template = Template(eval(f'{template_name}.html'))
        output_html = template.render(data)
        html_file = open("{output_path}/{file_name}", "w", encoding="utf-8")
        html_file.write(output_html)
        html_file.close()
