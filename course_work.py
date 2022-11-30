import json
import os
from pprint import pprint

from data import VK_TOKEN, YA_TOKEN, user_id

from progress.bar import IncrementalBar

import requests


class Backup:
    def __init__(self, vk_id, vk_token, ya_token, version='5.131'):
        self.vk_id = vk_id
        self.vk_token = vk_token
        self.ya_token = ya_token
        self.version = version
        self.vk_params = {
            'access_token': self.vk_token,
            'owner_id': self.vk_id,
            'album_id': 'profile',
            'rev': 1,
            'extended': 1,
            'photo_sizes': 1,
            'count': 5,
            'v': self.version,
        }

    def get_data(self):
        bar = IncrementalBar('Фотографий загруженно на пк (из 5): ', max=5)
        try:
            os.mkdir('img')
            print('Папка создана в рабочей области')
        except Exception:
            print('Папка уже была создана в рабочей области')
        url = 'https://api.vk.com/method/photos.get'
        req = requests.get(url=url, params=self.vk_params)
        req_json = req.json()
        data_list = []
        for item in req_json['response']['items']:
            data_dict = {}
            name = item['likes']['count']
            for i in data_list:
                if name in i.values():
                    name = item['date']
                    data_dict['file_name'] = f'{name}.jpg'
            data_dict['file_name'] = f'{name}.jpg'
            with open(f'img/{name}.jpg', 'wb') as file:
                for size in item['sizes']:
                    response = requests.get(url=item['sizes'][-1]['url']).content
                    file.write(response)
                    data_dict['size'] = item['sizes'][-1]['type']
            data_list.append(data_dict)
            bar.next()
        bar.finish()
        with open('data.json', 'w', encoding='utf-8') as file:
            json.dump(data_list, file, indent=4, ensure_ascii=False)
        with open('data.json', encoding='utf-8') as file:
            data = json.load(file)
        pprint(data)

    def create_folder(self):
        try:
            url = 'https://cloud-api.yandex.net/v1/disk/resources'
            params = {
                'path': 'img'
            }
            headers = {
                'Authorization': f'OAuth {self.ya_token}',
            }
            req = requests.put(url=url, params=params, headers=headers)
            req.raise_for_status()
            print('Папка создана в облачном хранилище')
        except Exception:
            print('Папка уже была создана в облачном хранилище')

    def upload_data(self, file_path, file_data):
        url = 'https://cloud-api.yandex.net/v1/disk/resources/upload'
        params = {
            'path': 'img/' + file_path,
            'overwrite': 'true',
        }
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'OAuth {self.ya_token}',
        }
        req = requests.get(url=url, headers=headers, params=params)
        href = req.json().get('href')
        req = requests.put(href, data=file_data)
        req.raise_for_status()


def main():
    back = Backup(vk_id=user_id, vk_token=VK_TOKEN, ya_token=YA_TOKEN)
    back.get_data()
    bar = IncrementalBar('Фотографий выгруженно (из 5): ', max=5)
    back.create_folder()
    with open('data.json', encoding='utf-8') as file:
        file_data = json.load(file)
        for data in file_data:
            file_path = data['file_name']
            with open(f'img/{file_path}', 'rb') as file:
                file_data = file.read()
                back.upload_data(file_path, file_data)
                bar.next()
        bar.finish()


if __name__ == '__main__':
    main()
