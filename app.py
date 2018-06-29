# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

import json
import os
import re
import sys
from argparse import ArgumentParser
from re import Match

from flask import Flask, request, abort
from jinja2 import Environment, FileSystemLoader, select_autoescape
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError,
    LineBotApiError
)
from linebot.models import (
    MessageEvent, TextMessage,
    FlexSendMessage, BubbleContainer, CarouselContainer, TextSendMessage
)

import qiita

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
handler = WebhookHandler(channel_secret)

template_env = Environment(
    loader=FileSystemLoader('templates'),
    autoescape=select_autoescape(['html', 'xml', 'json'])
)


class TextPatternHandler:

    def __init__(self):
        self.handlers = []

    def add(self, pattern: str):
        def decorator(func):
            self.handlers.append((re.compile(pattern), func))
            return func
        return decorator

    def handle(self, event: MessageEvent):

        text = event.message.text

        for pattern, func in self.handlers:
            m = pattern.match(text)
            if m:
                func(event, m)
                return True

        return False


text_pattern_handler = TextPatternHandler()


@app.route('/')
def index():
    return 'It worked!'


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    except LineBotApiError as e:
        app.logger.exception(f'LineBotApiError: {e.status_code} {e.message}', e)
        raise e

    return 'OK'


@handler.add(MessageEvent, message=TextMessage)
def message_text(event):

    try:
        replied = text_pattern_handler.handle(event)

        if not replied:
            line_bot_api.reply_message(
                event.reply_token,
                TextSendMessage('ちょっと何言ってるかわからない')
            )

    except Exception:
        line_bot_api.reply_message(
            event.reply_token,
            TextSendMessage('エラーです')
        )
        raise


@text_pattern_handler.add(pattern=r'^items$')
def reply_items(event: MessageEvent, match: Match):

    items = qiita.get_items(10)

    template = template_env.get_template('items.json')
    data = template.render(dict(items=items))

    print(data)

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
            alt_text="items",
            contents=CarouselContainer.new_from_json_dict(json.loads(data))
        )
    )


@text_pattern_handler.add(pattern=r'^users/(.+)$')
def reply_user(event: MessageEvent, match: Match):

    user_name = match.group(1)

    items = qiita.get_user_items(user_name, 3)
    user = items[0].user

    template = template_env.get_template('user.json')
    data = template.render(dict(user=user, items=items))

    print(data)

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
            alt_text='user',
            contents=BubbleContainer.new_from_json_dict(json.loads(data))
        )
    )


@text_pattern_handler.add(pattern=r'^tags/(.+)$')
def reply_tag(event: MessageEvent, match: Match):

    tag_name = match.group(1)

    tag = qiita.get_tag(tag_name)
    items = qiita.get_tag_items(tag_name, 5)

    template = template_env.get_template('tag.json')
    data = template.render(dict(tag=tag, items=items))

    print(data)

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
            alt_text='tag',
            contents=CarouselContainer.new_from_json_dict(json.loads(data))
        )
    )


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
