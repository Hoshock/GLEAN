# coding:UTF-8
from collections import OrderedDict

class Point(object):
    def __init__(self, z, x, y):
        self.name = 'point'
        self.z    = z
        self.x    = x
        self.y    = y
        
        self.params = OrderedDict([('z', self.z), ('x', self.x), ('y', self.y)])
        self.opt    = OrderedDict([('z', 0), ('x', 1), ('y', 1)])

    def __str__(self):
        return '{0}\t{1:.6e}\t{2:.6e}\t{3:.6e}\n'.format(self.name, self.z, self.x, self.y)

MODEL_LIST = {'point': Point}
