# coding=utf-8
from aip import AipOcr
from Config import config


def Distinguish():
    item, path = [], './Static/Img/sample.png'
    client = AipOcr(config.AppID, config.ApiKey, config.SecretKey)
    with open(path, 'rb') as f:
        image = f.read()
    json = client.basicGeneral(image)
    data_list = json['words_result']
    for data in data_list:
        item.append(data['words'])
    return ''.join(item)


if __name__ == '__main__':
    Distinguish()
