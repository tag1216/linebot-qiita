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
import typing
from argparse import ArgumentParser
from itertools import repeat
from re import Match

from flask import Flask, request, abort

import qiita
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError,
    LineBotApiError)
from linebot.models import (
    MessageEvent, TextMessage,
    FlexSendMessage, BubbleContainer, BoxComponent, TextComponent, CarouselContainer, ImageComponent, FillerComponent,
    SeparatorComponent, MessageAction, TextSendMessage)

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

    message = FlexSendMessage(
        alt_text="flex",
        contents=CarouselContainer(
            contents=[
                create_items_content(item)
                for item in items
            ]
        )
    )

    print(json.dumps(message.as_json_dict(), indent=2, sort_keys=True, ensure_ascii=False))

    line_bot_api.reply_message(event.reply_token, message)


@text_pattern_handler.add(pattern=r'^users/(.+)$')
def reply_user(event: MessageEvent, match: Match):

    user_name = match.group(1)

    items = qiita.get_user_items(user_name, 3)
    user = items[0].user

    contents = create_user_content(user, items)

    print(json.dumps(contents.as_json_dict(), indent=2, sort_keys=True, ensure_ascii=False))

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
            alt_text='flex',
            contents=contents
        )
    )


@text_pattern_handler.add(pattern=r'^tags/(.+)$')
def reply_tag(event: MessageEvent, match: Match):

    tag_name = match.group(1)

    tag = qiita.get_tag(tag_name)
    items = qiita.get_tag_items(tag_name, 5)

    contents = create_tag_content(tag, items)

    print(json.dumps(contents.as_json_dict(), indent=2, sort_keys=True, ensure_ascii=False))

    line_bot_api.reply_message(
        event.reply_token,
        FlexSendMessage(
            alt_text='flex',
            contents=contents
        )
    )


def create_items_content(item: qiita.Item):
    return BubbleContainer(
        header=BoxComponent(
            layout='vertical',
            contents=[
                BoxComponent(
                    layout='horizontal',
                    contents=[
                        TextComponent(
                            flex=0,
                            size='xxs',
                            color='#aaaaaa',
                            text=f'{item.created_at}に投稿'
                        ),
                        FillerComponent(),
                        TextComponent(
                            flex=0,
                            size='xxs',
                            color='#aaaaaa',
                            text=f'{item.likes_count}いいね'
                        )
                    ]
                ),
                TextComponent(
                    weight='bold',
                    size='lg',
                    color='#aaaaaa',
                    text=item.user.id
                ),
            ],
        ),
        hero=ImageComponent(
            url=item.user.profile_image_url,
            action=user_action(item.user.id)
        ),
        body=BoxComponent(
            layout='vertical',
            spacing='sm',
            contents=[
                TextComponent(
                    text=item.title,
                    wrap=True,
                    weight='bold',
                    color='#444444',
                    size='lg'
                ),
                BoxComponent(
                    layout='horizontal',
                    spacing='sm',
                    contents=[
                        TextComponent(
                            flex=0,
                            size='sm',
                            color='#aaaaaa',
                            text=tag.name,
                            action=tag_action(tag.name)
                        )
                        for tag in item.tags
                    ]
                )
            ]
        )
    )


def create_user_content(user: qiita.User, items: typing.List[qiita.Item]):

    contents = [create_user_item_content(item) for item in items]
    separator = SeparatorComponent()
    contents = sum(map(list, zip(contents, repeat(separator))), [])[:-1]

    return BubbleContainer(
        header=BoxComponent(
            layout='vertical',
            contents=[
                TextComponent(
                    text=user.id,
                    weight='bold',
                    color='#aaaaaa',
                    size='lg'
                )
            ]
        ),
        hero=ImageComponent(
            size='lg',
            url=user.profile_image_url
        ),
        body=BoxComponent(
            layout='vertical',
            spacing='sm',
            contents=[
                TextComponent(
                    wrap=True,
                    text=user.description or ' '
                ),
                SeparatorComponent()
            ] + contents
        )
    )


def create_user_item_content(item):
    return BoxComponent(
        layout='vertical',
        contents=[
            TextComponent(
                margin='md',
                size='xxs',
                color='#aaaaaa',
                text=f'{item.created_at}に投稿'
            ),
            TextComponent(
                size='sm',
                text=item.title,
            ),
            BoxComponent(
                layout='horizontal',
                spacing='sm',
                contents=[
                    TextComponent(
                        flex=0,
                        size='sm',
                        color='#aaaaaa',
                        text=tag.name,
                        action=tag_action(tag.name)
                    )
                    for tag in item.tags
                ]
            ),
            BoxComponent(
                layout='horizontal',
                spacing='sm',
                contents=[
                    FillerComponent(),
                    TextComponent(
                        flex=0,
                        size='xxs',
                        color='#aaaaaa',
                        text=f'{item.likes_count}いいね'
                    )
                ]
            )
        ]
    )


def create_tag_content(tag, items):
    return CarouselContainer(
        contents=[
            BubbleContainer(
                header=BoxComponent(
                    layout='vertical',
                    contents=[
                        TextComponent(
                            text=tag.id,
                            weight='bold',
                            color='#aaaaaa',
                            size='lg'
                        ),
                        TextComponent(
                            text=f'{tag.items_count} items, {tag.followers_count} followers',
                            color='#aaaaaa',
                            size='xxs'
                        )
                    ]
                ),
                hero=ImageComponent(
                    size='md',
                    url=tag.icon_url
                ),
                body=BoxComponent(
                    layout='vertical',
                    spacing='sm',
                    contents=[
                        BoxComponent(
                            layout='horizontal',
                            contents=[
                                ImageComponent(
                                    url=item.user.profile_image_url,
                                    size='sm',
                                    action=tag_action(tag.id)
                                ),
                                BoxComponent(
                                    layout='vertical',
                                    contents=[
                                        TextComponent(
                                            text=item.title,
                                            wrap=True,
                                            size='sm',
                                        )
                                    ]
                                )
                            ]
                        )
                        for item in items
                    ]
                ),
            )
        ]
    )


def user_action(user_id):
    return MessageAction(
        text=f'users/{user_id}'
    )


def tag_action(tag_name):
    return MessageAction(
        text=f'tags/{tag_name}'
    )


if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
