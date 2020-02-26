import requests
import os
import pathvalidate
import bs4
import urllib.parse
import json
import sys
import argparse
from pathvalidate import sanitize_filename
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from dotenv import load_dotenv


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--start_page', type=int, default=1)
    parser.add_argument('--end_page', type=int, default=sys.maxsize**10)
    return parser


def download_txt(txt_url, book_title, folder):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(txt_url, allow_redirects=False)
    response.raise_for_status()

    if response.status_code == 200:
        book_path = os.path.join(folder, sanitize_filename(book_title+'.txt'))
        with open(book_path, 'wb') as file:
            file.write(response.content)
        books_characteristics['book_path'] = book_path
        return book_path


def download_image(img_url, image_name, folder):
    os.makedirs(folder, exist_ok=True)
    response = requests.get(img_url, allow_redirects=False)
    response.raise_for_status()

    if response.status_code == 200:
        image_src = os.path.join(folder, sanitize_filename(image_name))
        with open(image_src, 'wb') as file:
            file.write(response.content)
        books_characteristics['image_src'] = image_src
        return image_src


def create_json_catalogue(json_catalogue):
    with open(json_catalogue, "w", encoding='utf8') as my_file:
        json.dump(books_catalogue,my_file, indent="   ",ensure_ascii=False)


if __name__ == "__main__":
    load_dotenv()
    books_folder = os.getenv('books_folder')
    images_folder = os.getenv('images_folder')
    json_catalogue = os.getenv('json_catalogue')

    url = 'http://tululu.org'
    books_catalogue = []

    parser = create_parser()
    namespace = parser.parse_args(sys.argv[1:])


    for page_num in range(namespace.start_page, namespace.end_page):
        page_url = urljoin(url, ('l55/{page_num}/'.format(page_num=page_num)))
        page_response = requests.get(page_url, allow_redirects=False)
        page_response.raise_for_status()

        if page_response.status_code == 200:
            page_soup = BeautifulSoup(page_response.text, 'lxml')

            books_selector = ".bookimage a"
            books_blocks = page_soup.select(books_selector)


            for book in books_blocks:
                books_urls = []
                book_link = urljoin(url, book['href'])
                books_urls.append(book_link)


                for book_url in books_urls:
                    response = requests.get(book_url, allow_redirects=False)
                    response.raise_for_status()


                    books_soup = BeautifulSoup(response.text, 'lxml')


                    book_id = book_url.split('/')[3].split('b')[1]

                    title_and_author_selector = "#content h1"
                    title_and_author = books_soup.select_one(title_and_author_selector).text.split("::")
                    book_title = title_and_author[0].strip()
                    book_author = title_and_author[1].strip()

                    books_characteristics = {'title': book_title}
                    books_characteristics['author'] = book_author


                    image_link_selector = ".bookimage a img"
                    img_src = books_soup.select_one(image_link_selector)['src']
                    image_link =  urljoin(url,img_src)
                    image_name = img_src.split('/')[2]


                    download_image(image_link, image_name, os.path.join(images_folder))

                    download_txt((urljoin(url, ("txt.php?id={id}".format(id=book_id)))), book_title, os.path.join(books_folder))


                    comments_selector = ".texts .black"
                    comments_blocks = books_soup.select(comments_selector)
                    comments = []
                    for comment in comments_blocks: comments.append(comment.text)

                    books_characteristics['comments'] = comments


                    genres_selector = "span.d_book a"
                    genres_blocks = books_soup.select(genres_selector)
                    genres = []
                    for genre in genres_blocks: genres.append(genre.text)

                    books_characteristics['genres'] = genres


                    books_catalogue.append(books_characteristics)
        else:
            break

    create_json_catalogue(json_catalogue)