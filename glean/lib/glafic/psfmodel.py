# coding:UTF-8
from collections import OrderedDict

class PSF(object):
    def __init__(self, fwhm_1, e_1, theta_e_1, beta_1, fwhm_2, e_2, theta_e_2, beta_2, frac):
        self.name      = 'psf'
        self.fwhm_1    = fwhm_1
        self.e_1       = e_1
        self.theta_e_1 = theta_e_1
        self.beta_1    = beta_1
        self.fwhm_2    = fwhm_2
        self.e_2       = e_2
        self.theta_e_2 = theta_e_2
        self.beta_2    = beta_2
        self.frac      = frac

        self.params  = OrderedDict([('fwhm_1', self.fwhm_1), ('e_1', self.e_1), ('theta_e_1', self.theta_e_1),
                                    ('beta_1', self.beta_1), ('fwhm_2', self.fwhm_2), ('e_2', self.e_2),
                                    ('theta_e_2', self.theta_e_2), ('beta_2', self.beta_2), ('frac', self.frac)])
        self.opt     = OrderedDict([('fwhm_1', 0), ('e_1', 0), ('theta_e_1', 0), ('beta_1', 0), ('fwhm_2', 0),
                                    ('e_2', 0), ('theta_e_2', 0), ('beta_2', 0), ('frac', 0)])

    def __str__(self):
        return '{0}\t{1:.6e}\t{2:.6e}\t{3:.6e}\t{4:.6e}\t{5:.6e}\t{6:.6e}\t{7:.6e}\t{8:.6e}\t{9:.6e}\n'.format(self.name,
                self.fwhm_1, self.e_1, self.theta_e_1, self.beta_1, self.fwhm_2, self.e_2, self.theta_e_2, self.beta_2, self.frac)

MODEL_LIST = {'psf': PSF}
