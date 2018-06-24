import dataclasses
import typing

import requests


@dataclasses.dataclass
class User:
    description: str
    facebook_id: str
    followees_count: int
    followers_count: int
    github_login_name: str
    id: str
    items_count: int
    linkedin_id: str
    location: str
    name: str
    organization: str
    permanent_id: int
    profile_image_url: str
    twitter_screen_name: str
    website_url: str


@dataclasses.dataclass
class ItemTag:
    name: str
    versions: typing.List[str]


@dataclasses.dataclass
class Item:
    rendered_body: str
    body: str
    coediting: bool
    comments_count: int
    created_at: str
    group: typing.Dict
    id: str
    likes_count: int
    private: bool
    reactions_count: int
    tags: typing.List[ItemTag]
    title: str
    updated_at: str
    url: str
    user: User
    page_views_count: int

    def __post_init__(self):
        if isinstance(self.user, dict):
            self.user = User(**self.user)
        self.tags = [ItemTag(**tag) if isinstance(tag, dict) else tag for tag in self.tags]


@dataclasses.dataclass
class Tag:
    followers_count: int
    icon_url: str
    id: str
    items_count: int


def get_items(per_page=10):

    response = requests.get(
        'https://qiita.com/api/v2/items',
        params=dict(per_page=per_page)
    )
    data = response.json()

    items = [Item(**row) for row in data]

    return items


def get_user_items(user_name, per_page=10):

    response = requests.get(
        f'https://qiita.com/api/v2/users/{user_name}/items',
        params=dict(per_page=per_page)
    )
    data = response.json()

    items = [Item(**row) for row in data]

    return items


def get_tag_items(tag_name, per_page=10):

    response = requests.get(
        f'https://qiita.com/api/v2/tags/{tag_name}/items',
        params=dict(per_page=per_page)
    )
    data = response.json()

    items = [Item(**row) for row in data]

    return items


def get_tag(tag_name):

    response = requests.get(
        f'https://qiita.com/api/v2/tags/{tag_name}'
    )
    data = response.json()

    tag = Tag(**data)

    return tag