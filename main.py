import json
import requests
import datetime
from discord import Intents
from bs4 import BeautifulSoup
from discord.ext import commands, tasks
from dotenv import load_dotenv
import os

# .envファイルをロード
load_dotenv()

# 環境変数の値を取得
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")
QIITA_ORGANIZATION_NAME = os.getenv("QIITA_ORGANIZATION_NAME")

bot = commands.Bot(command_prefix="!", intents=Intents.default())


async def send_new_posts(posts, last_check_time):
    for post in posts:
        created_at = datetime.datetime.fromisoformat(
            post["publishedAt"].replace("Z", "+00:00")
        )
        if created_at > last_check_time:
            title = post["title"]
            url = post["linkUrl"]
            author = post["author"]["name"]
            message = f"新しい投稿があります: {title} by {author}\n{url}"
            channel = bot.get_channel(DISCORD_CHANNEL_ID)
            await channel.send(message)


def fetch_posts():
    url = f"https://qiita.com/organizations/{QIITA_ORGANIZATION_NAME}/items?page=1"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")

    items_data = soup.find(
        "script",
        {"type": "application/json", "data-component-name": "OrganizationsItemsPage"},
    ).get_text()
    items_json = json.loads(items_data)
    return items_json["organization"]["paginatedOrganizationArticles"]["items"]


@bot.event
async def on_ready():
    print(f"{bot.user} has connected to Discord!")
    check_new_posts.start()


@tasks.loop(minutes=5)
async def check_new_posts():
    last_check_time = datetime.datetime.utcnow().replace(
        tzinfo=datetime.timezone.utc
    ) - datetime.timedelta(minutes=5)

    posts = fetch_posts()
    await send_new_posts(posts, last_check_time)


if __name__ == "__main__":
    bot.run(DISCORD_TOKEN)
