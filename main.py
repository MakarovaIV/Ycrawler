import asyncio
from hashlib import shake_256

import aiofiles
import aiohttp
import logging
import os
import re
import time
import uuid
from bs4 import BeautifulSoup

URL = "https://news.ycombinator.com"
Y_LINK = 'ycombinator.com'
DOWNLOAD_DIR = "/tmp/ycrawler"
CYCLE_TIMEOUT = 10 #sec
REQUEST_TIMEOUT = 5 #sec


async def write_to_file(filename, content):
    async with aiofiles.open(filename, "w") as f:
        await f.write(content)


def generate_name_from_link(url):
    return "/" + shake_256(url.encode()).hexdigest(10)


async def find_news_blocks(session, url):
    blocks = []
    try:
        page = await session.get(url, timeout=REQUEST_TIMEOUT)
        page = await page.text()
        soup = BeautifulSoup(page, "html.parser")
        news_headers = soup.findAll('tr', class_='athing')
        for tr in news_headers:
            comments_block = tr.findNextSibling('tr')
            comment_link = comments_block.find('a', string=re.compile('comment(s|)$'))
            news_link = tr.find('span', class_='titleline')
            news_link = news_link.a if news_link else None
            news_link = news_link['href'] if news_link else None
            if news_link is not None and 'http' != news_link[:4]:
                news_link = URL + '/' + news_link

            block = {'news_link': news_link,
                     'comment_link': (URL + '/' + comment_link['href']) if comment_link else None}
            blocks.append(block)
        return blocks
    except Exception as e:
        logging.warning("Cannot find news and comments block in {}".format(url))
        return []


async def get_content(session, url):
    content = ''
    try:
        response = await session.get(url, timeout=REQUEST_TIMEOUT)
        content = await response.text()
    except Exception as e:
        logging.warning("No response from {}".format(url))
    return content


def filter_link(link):
    if 'http' != link[:4]:
        return False
    if Y_LINK in link:
        return False
    return True


async def get_external_link_from_page(session, url):
    try:
        page = await session.get(url, timeout=REQUEST_TIMEOUT)
        page = await page.text()
        soup = BeautifulSoup(page, "html.parser")
        all_links = map(lambda anchor: anchor['href'], soup.findAll('a'))
        return list(filter(filter_link, all_links))
    except Exception as e:
        logging.warning("No response from comment link ({})".format(url))
        return []


def create_dir(abs_path):
    if not os.path.exists(abs_path):
        os.makedirs(abs_path)


async def save_url_to_disk(session, url, abs_path):
    content = await get_content(session, url) or 'No response from server'
    await write_to_file(abs_path, content)


# def get_dir_name(path):
#     list_of_existed_dir = []
#     for directories in os.walk(path):
#         for name in directories:
#             list_of_existed_dir.append(os.path.join(name))
#     return list_of_existed_dir


# def is_downloaded(dir_name, path):
#     return dir_name in os.listdir(path)


async def worker(session):
    start_time = time.time()
    print("start time: ", start_time)
    all_news = await find_news_blocks(session, URL)

    for news in all_news:
        news_link = news['news_link']
        if news_link:
            dir_name = generate_name_from_link(news_link)
            if dir_name in os.listdir(DOWNLOAD_DIR):
                logging.warning("URL {} is already downloaded".format(news_link))
            else:
                news_dir_name = DOWNLOAD_DIR + dir_name
                create_dir(news_dir_name)
                news_filename = news_dir_name + dir_name + '.html'
                await save_url_to_disk(session, news_link, news_filename)
                comment = news['comment_link']
                if comment:
                    comment_links = await get_external_link_from_page(session, comment)
                    for link in comment_links:
                        comment_dir_name = news_dir_name + '/comments'
                        create_dir(comment_dir_name)
                        comment_filename = comment_dir_name + generate_name_from_link(link) + '.html'
                        await save_url_to_disk(session, link, comment_filename)
    end_time = time.time()
    print("finished at: ", end_time)
    print("duration: ", end_time - start_time)


async def main():
    async with aiohttp.ClientSession() as session:
        while True:
            await worker(session)
            await asyncio.sleep(CYCLE_TIMEOUT)


if __name__ == '__main__':
    asyncio.run(main())

