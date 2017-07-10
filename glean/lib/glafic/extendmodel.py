# coding:UTF-8
from collections import OrderedDict

class Gauss(object):
    def __init__(self, z, Sigma0, x, y, e, theta_e, sigma, p8):
        self.name    = 'gauss'
        self.z       = z
        self.Sigma0  = Sigma0
        self.x       = x
        self.y       = y
        self.e       = e
        self.theta_e = theta_e
        self.sigma   = sigma

        self.params  = OrderedDict([('z', self.z), ('Sigma0', self.Sigma0), ('x', self.x), ('y', self.y),
                                    ('e', self.e), ('theta_e', self.theta_e), ('sigma', self.sigma)])
        self.opt     = OrderedDict([('z', 0), ('Sigma0', 0), ('x', 0), ('y', 0),
                                    ('e', 0), ('theta_e', 0), ('sigma', 0), ('p8', 0)])

    def __str__(self):
        return 'extend\t{0}\t{1:.6e}\t{2:.6e}\t{3:.6e}\t{4:.6e}\t{5:.6e}\t{6:.6e}\t{7:.6e}\t{8:.6e}\n'.format(self.name, 
                self.z, self.Sigma0, self.x, self.y, self.e, self.theta_e, self.sigma, 0)

MODEL_LIST = {'gauss': Gauss}
