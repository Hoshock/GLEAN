# coding:UTF-8
from collections import OrderedDict

class SIE(object):
    def __init__(self, sigma, x, y, e, theta_e, r_core, p7):
        self.name    = 'sie'
        self.sigma   = sigma
        self.x       = x
        self.y       = y
        self.e       = e
        self.theta_e = theta_e
        self.r_core  = r_core

        self.params  = OrderedDict([('sigma', self.sigma), ('x', self.x), ('y', self.y),
                                    ('e', self.e), ('theta_e', self.theta_e), ('r_core', self.r_core)])
        self.opt     = OrderedDict([('sigma', 0), ('x', 0), ('y', 0), ('e', 0),
                                    ('theta_e', 0), ('r_core', 0), ('p7', 0)])

    def __str__(self):
        return 'lens\t{0}\t{1:.6e}\t{2:.6e}\t{3:.6e}\t{4:.6e}\t{5:.6e}\t{6:.6e}\t{7:.6e}\n'.format(self.name,
                self.sigma, self.x, self.y, self.e, self.theta_e, self.r_core, 0)

        
class Pert(object):
    def __init__(self, z, x, y, gamma, theta_gamma, p6, kappa):
        self.name        = 'pert'
        self.z           = z
        self.x           = x
        self.y           = y
        self.gamma       = gamma
        self.theta_gamma = theta_gamma
        self.kappa       = kappa

        self.params      = OrderedDict([('z', self.z), ('x', self.x), ('y', self.y),
                                        ('gamma', self.gamma), ('theta_gamma', self.theta_gamma), ('kappa', self.kappa)])
        self.opt         = OrderedDict([('z', 0), ('x', 0), ('y', 0), ('gamma', 0),
                                        ('theta_gamma', 0), ('p6', 0), ('kappa', 0)])
        
    def __str__(self):
        return 'lens\t{0}\t{1:.6e}\t{2:.6e}\t{3:.6e}\t{4:.6e}\t{5:.6e}\t{6:.6e}\t{7:.6e}\n'.format(self.name,
                self.z, self.x, self.y, self.gamma, self.theta_gamma, 0, self.kappa)

class Clus3(object):
    def __init__(self, z, x, y, delta, theta_delta, p6, p7):
        self.name        = 'clus3'
        self.z           = z
        self.x           = x
        self.y           = y
        self.delta       = delta
        self.theta_delta = theta_delta

        self.params      = OrderedDict([('z', self.z), ('x', self.x), ('y', self.y),
                                        ('delta', self.delta), ('theta_delta', self.theta_delta)])
        self.opt         = OrderedDict([('z', 0), ('x', 0), ('y', 0), ('delta', 0),
                                        ('theta_delta', 0), ('p6', 0), ('p7', 0)])
        
    def __str__(self):
        return 'lens\t{0}\t{1:.6e}\t{2:.6e}\t{3:.6e}\t{4:.6e}\t{5:.6e}\t{6:.6e}\t{7:.6e}\n'.format(self.name,
                self.z, self.x, self.y, self.delta, self.theta_delta, 0, 0)

class Mpole(object):
    def __init__(self, z, x, y, epsilon, theta_m, m, n):
        self.name    = 'mpole'
        self.z       = z
        self.x       = x
        self.y       = y
        self.epsilon = epsilon
        self.theta_m = theta_m
        self.m       = m
        self.n       = n

        self.params  = OrderedDict([('z', self.z), ('x', self.x), ('y', self.y),
                                    ('epsilon', self.epsilon), ('theta_m', self.theta_m), ('m', self.m), ('n', self.n)])
        self.opt     = OrderedDict([('z', 0), ('x', 0), ('y', 0), ('epsilon', 0),
                                    ('theta_m', 0), ('m', 0), ('n', 0)])

    def __str__(self):
        return 'lens\t{0}\t{1:.6e}\t{2:.6e}\t{3:.6e}\t{4:.6e}\t{5:.6e}\t{6:.6e}\t{7:.6e}\n'.format(self.name,
                self.z, self.x, self.y, self.epsilon, self.theta_m, self.m, self.n)


class Pow(object):
    def __init__(self, z, x, y, e, theta_e, r_ein, gamma):
        self.name    = 'pow'
        self.z       = z
        self.x       = x
        self.y       = y
        self.e       = e
        self.theta_e = theta_e
        self.r_ein   = r_ein
        self.gamma   = gamma

        self.params  = OrderedDict([('z', self.z), ('x', self.x), ('y', self.y),
                                    ('e', self.e), ('theta_e', self.theta_e), ('r_ein', self.r_ein), ('gamma', self.gamma)])
        self.opt     = OrderedDict([('z', 0), ('x', 0), ('y', 0), ('e', 0),
                                    ('theta_e', 0), ('r_ein', 0), ('gamma', 0)])

    def __str__(self):
        return 'lens\t{0}\t{1:.6e}\t{2:.6e}\t{3:.6e}\t{4:.6e}\t{5:.6e}\t{6:.6e}\t{7:.6e}\n'.format(self.name,
                self.z, self.x, self.y, self.e, self.theta_e, self.r_ein, self.gamma)

    
class Powpot(object):
    def __init__(self, z, x, y, e_p, theta_e, r_ein, gamma):
        self.name    = 'powpot'
        self.z       = z
        self.x       = x
        self.y       = y
        self.e_p     = e_p
        self.theta_e = theta_e
        self.r_ein   = r_ein
        self.gamma   = gamma

        self.params  = OrderedDict([('z', self.z), ('x', self.x), ('y', self.y),
                                    ('e_p', self.e_p), ('theta_e', self.theta_e), ('r_ein', self.r_ein), ('gamma', self.gamma)])
        self.opt     = OrderedDict([('z', 0), ('x', 0), ('y', 0), ('e', 0),
                                    ('theta_e', 0), ('r_ein', 0), ('gamma', 0)])

    def __str__(self):
        return 'lens\t{0}\t{1:.6e}\t{2:.6e}\t{3:.6e}\t{4:.6e}\t{5:.6e}\t{6:.6e}\t{7:.6e}\n'.format(self.name,
                self.z, self.x, self.y, self.e_p, self.theta_e, self.r_ein, self.gamma)

MODEL_LIST = {'sie': SIE, 'pert': Pert, 'clus3': Clus3, 'mpole': Mpole, 'pow': Pow, 'powpot': Powpot}
