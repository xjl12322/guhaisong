# coding=utf-8
import os
from FontCracks import FontCrack

path = os.path.dirname(__file__)


class Font:
    def __init__(self):
        self.Crack = FontCrack.Crack()

    def CharDecrypt(self, key):
        if os.path.exists(path + '/fonts/{}.dict'.format(key)):
            with open(path + '/fonts/{}.dict'.format(key), 'r', encoding='utf-8') as f:
                mapping = f.read()
            try:
                map = eval(mapping)
            except:
                print('mapping错误',mapping)
                map = {}
            return map
        else:
            mapping = self.Crack.CharDecrypt(key)
            if mapping is None:
                return
            with open(path + '/fonts/{}.dict'.format(key), 'w', encoding='utf-8') as f:
                f.write(str(mapping))
            return mapping

    def NumDecrypt(self, key):
        if os.path.exists(path + '/fonts/{}_num.dict'.format(key)):
            with open(path + '/fonts/{}_num.dict'.format(key), 'r', encoding='utf-8') as f:
                mapping = f.read()
            return eval(mapping)
        else:
            mapping = self.Crack.NumDecrypt(key)
            if mapping is None:
                return
            with open(path + '/fonts/{}_num.dict'.format(key), 'w+', encoding='utf-8') as f:
                f.write(str(mapping))
            return mapping


if __name__ == '__main__':
    start = Font()
    start.CharDecrypt('d08659e4')
    # start.CharDecrypt('0c453b7a')
