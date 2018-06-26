import os
import typing
from abc import ABCMeta

import requests
from future.utils import with_metaclass
from linebot.models import Base


access_token = os.getenv('QIITA_ACCESS_TOKEN', None)

headers = {}
if access_token:
    headers.update({
        "Authorization": f"Bearer {access_token}"
    })


class User(with_metaclass(ABCMeta, Base)):

    def __init__(
            self,
            description: str,
            facebook_id: str,
            followees_count: int,
            followers_count: int,
            github_login_name: str,
            id: str,
            items_count: int,
            linkedin_id: str,
            location: str,
            name: str,
            organization: str,
            permanent_id: int,
            profile_image_url: str,
            twitter_screen_name: str,
            website_url: str,
    ):
        self.description = description
        self.facebook_id = facebook_id
        self.followees_count = followees_count
        self.followers_count = followers_count
        self.github_login_name = github_login_name
        self.id = id
        self.items_count = items_count
        self.linkedin_id = linkedin_id
        self.location = location
        self.name = name
        self.organization = organization
        self.permanent_id = permanent_id
        self.profile_image_url = profile_image_url
        self.twitter_screen_name = twitter_screen_name
        self.website_url = website_url


class ItemTag(with_metaclass(ABCMeta, Base)):

    def __init__(self, name, versions):
        self.name = name
        self.versions = versions


class Item(with_metaclass(ABCMeta, Base)):

    def __init__(
            self,
        rendered_body: str,
        body: str,
        coediting: bool,
        comments_count: int,
        created_at: str,
        group: typing.Dict,
        id: str,
        likes_count: int,
        private: bool,
        reactions_count: int,
        tags: typing.List[ItemTag],
        title: str,
        updated_at: str,
        url: str,
        user: User,
        page_views_count: int
    ):
        self.rendered_body = rendered_body
        self.body = body
        self.coediting = coediting
        self.comments_count = comments_count
        self.created_at = created_at
        self.group = group
        self.id = id
        self.likes_count = likes_count
        self.private = private
        self.reactions_count = reactions_count
        self.tags = [ItemTag.new_from_json_dict(tag) for tag in tags]
        self.title = title
        self.updated_at = updated_at
        self.url = url
        self.user = User.new_from_json_dict(user)
        self.page_views_count = page_views_count


class Tag(with_metaclass(ABCMeta, Base)):

    def __init__(
            self,
            followers_count: int,
            icon_url: str,
            id: str,
            items_count: int
    ):
        self.followers_count = followers_count
        self.icon_url = icon_url
        self.id = id
        self.items_count = items_count


def get_items(per_page=10):

    response = requests.get(
        'https://qiita.com/api/v2/items',
        headers=headers,
        params=dict(per_page=per_page)
    )
    data = response.json()

    items = [Item.new_from_json_dict(row) for row in data]

    return items


def get_user_items(user_name, per_page=10):

    response = requests.get(
        f'https://qiita.com/api/v2/users/{user_name}/items',
        headers=headers,
        params=dict(per_page=per_page)
    )
    data = response.json()

    items = [Item.new_from_json_dict(row) for row in data]

    return items


def get_tag_items(tag_name, per_page=10):

    response = requests.get(
        f'https://qiita.com/api/v2/tags/{tag_name}/items',
        headers=headers,
        params=dict(per_page=per_page)
    )
    data = response.json()

    items = [Item.new_from_json_dict(row) for row in data]

    return items


def get_tag(tag_name):

    response = requests.get(
        f'https://qiita.com/api/v2/tags/{tag_name}',
        headers=headers
    )
    data = response.json()

    tag = Tag.new_from_json_dict(data)

    return tag
