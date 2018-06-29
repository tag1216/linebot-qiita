import unittest

from jinja2 import Environment, FileSystemLoader, select_autoescape

import qiita


class TemplateTest(unittest.TestCase):

    def setUp(self):
        self.env = Environment(
            loader=FileSystemLoader('templates'),
            autoescape=select_autoescape(['html', 'xml', 'json'])
        )

    def test_items(self):

        items = qiita.get_items(1)

        template = self.env.get_template('items.json')
        text = template.render(dict(items=items))
        print(text)

    def test_user(self):

        items = qiita.get_user_items('tag1216', 1)
        user = items[0].user

        template = self.env.get_template('user.json')
        text = template.render(dict(user=user, items=items))
        print(text)

    def test_tag(self):

        tag = qiita.get_tag('python')
        items = qiita.get_tag_items('python', 2)

        template = self.env.get_template('tag.json')
        text = template.render(dict(tag=tag, items=items))
        print(text)
