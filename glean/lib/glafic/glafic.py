# coding:UTF-8

import numpy as np
from subprocess import Popen, PIPE
from collections import OrderedDict
from copy import deepcopy

import lensmodel
reload(lensmodel)
import extendmodel
reload(extendmodel)
import pointmodel
reload(pointmodel)
import psfmodel
reload(psfmodel)

class GlaficError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class GlaficParams(object):
    GREEN_COLOR  = '\033[92m'
    YELLOW_COLOR = '\033[93m'
    RED_COLOR    = '\033[91m'
    CLEAR_COLOR  = '\033[0m'

    ERROR_CODE   = -1

    def __init__(self):
        self.default_primary_params   = OrderedDict([('omega', 0.26), ('lambda', 0.74), ('weos', -1.0),
                                                     ('hubble', 0.72), ('zl', 0.3), ('prefix', '../out/out'),
                                                     ('xmin', -60.0), ('ymin', -60.0), ('xmax', 60.0),
                                                     ('ymax', 60.0), ('pix_ext', 0.2), ('pix_poi', 3.0),
                                                     ('maxlev', 6)])
        self.default_secondary_params = OrderedDict([('galfile', 'galfile.dat'),
                                                     ('srcfile', 'srcfile.dat'),
                                                     ('ran_seed', -1234), ('outformat_exp', 0),
                                                     ('flag_hodensity', 0), ('hodensity', 200.0),
                                                     ('gnfw_usetab', 1), ('ein_usetab', 1), ('nfw_users', 0),
                                                     ('flag_extnorm', 0), ('chi2_checknimg', 1),
                                                     ('chi2_splane', 0), ('chi2_usemag', 0), ('chi2_restart', 0),
                                                     ('obs_gain', 3.0), ('obs_ncomb', 1), ('obs_readnoise', 10.0),
                                                     ('skyfix', 0), ('skyfix_value', 1e10), ('psfconv_size', 4.0),
                                                     ('seeing_sub', 1), ('flag_srcsbin', 1), ('srcsbinsize', 20.0),
                                                     ('flag_mcmcall', 0), ('addwcs', 0), ('wcs_ra0', 150.0),
                                                     ('wcs_dec0', 30.0), ('ovary', 0), ('lvary', 0),
                                                     ('wvary', 0), ('hvary', 0)])
        self.default_all_params       = OrderedDict(self.default_primary_params)
        self.default_all_params.update(self.default_secondary_params)

        self.primary_params   = OrderedDict(self.default_primary_params)
        self.secondary_params = OrderedDict(self.default_secondary_params)
        self.all_params       = OrderedDict(self.default_all_params)

    @classmethod
    def error(cls, err):
        print GlaficParams.RED_COLOR + 'Glaficparams error: ' + GlaficParams.CLEAR_COLOR + err

    def __getitem__(self, key):
        if key == 'all':
            return OrderedDict(self.all_params)
        elif key == 'primary':
            return OrderedDict(self.primary_params)
        elif key == 'secondary':
            return OrderedDict(self.secondary_params)
        elif key in self.all_params:
            return self.all_params[key]
        else:
            err = '{} does not exist.'.format(GlaficParams.YELLOW_COLOR + key + GlaficParams.CLEAR_COLOR)
            GlaficParams.error(err)
            return None

    def _convert_params(self, key, value):
        try:
            if isinstance(self.all_params[key], int):
                return int(value)
            elif isinstance(self.all_params[key], float):
                return float(value)
            elif isinstance(self.all_params[key], str):
                return value
        except ValueError:
            return None

    def _check_primary_params(self, key, value):
        if key in {'omega', 'lambda'}:
            return 0 <= value
        elif key in {'hubble', 'zl', 'pix_ext', 'pix_poi', 'maxlev'}:
            return 0 < value
        elif key in {'weos', 'prefix', 'xmin', 'ymin', 'xmax', 'ymax'}:
            return True

    def _check_secondary_params(self, key, value):
        if key in {'ran_seed', }:
            return value < 0
        elif key in {'outformat_exp', 'gnfw_usetab', 'ein_usetab', 'nfw_users', 'flag_extnorm',
                     'chi2_checknimg', 'chi2_splane', 'chi2_usemag', 'skyfix', 'flag_srcsbin',
                     'flag_mcmcall', 'addwcs', 'ovary', 'lvary', 'wvary', 'hvary'}:
            return value == 0 or value == 1
        elif key in {'flag_hodensity', }:
            return value == 0 or value == 1 or value == 2
        elif key in {'hodensity', 'obs_gain', 'obs_ncomb', 'obs_readnoise', 'skyfix_value',
                     'psfconv_size', 'srcsbinsize'}:
            return 0 < value
        elif key in {'chi2_restart', }:
            return -1 <= value
        elif key in {'seeing_sub', }:
            return 1 <= value
        elif key in {'galfile', 'srcfile', 'wcs_ra0', 'wcs_dec0'}:
            return True

    def __setitem__(self, key, value):
        if key not in self.all_params:
            err = '{} does not exist.'.format(GlaficParams.YELLOW_COLOR + key + GlaficParams.CLEAR_COLOR)
            GlaficParams.error(err)
            return GlaficParams.ERROR_CODE

        if key in self.primary_params:
            value_t = self._convert_params(key, value)
            if not self._check_primary_params(key, value_t):
                err = '{} is not a suitable value for {}.'.format(value, GlaficParams.YELLOW_COLOR + key + GlaficParams.CLEAR_COLOR)
                GlaficParams.error(err)
                return GlaficParams.ERROR_CODE

            if key == 'prefix':
                self.primary_params[key] = Glafic.OUT_DIR + value_t
                self.all_params[key]     = Glafic.OUT_DIR + value_t
            else:
                self.primary_params[key] = value_t
                self.all_params[key]     = value_t
        else:
            value_t = self._convert_params(key, value)
            if not self._check_secondary_params(key, value_t):
                err = '{} is not a suitable value for {}.'.format(value, GlaficParams.YELLOW_COLOR + key + GlaficParams.CLEAR_COLOR)
                GlaficParams.error(err)
                return GlaficParams.ERROR_CODE

            self.secondary_params[key] = value_t
            self.all_params[key]       = value_t

    def reset(self, key):
        if key == 'all':
            self.primary_params   = OrderedDict(self.default_primary_params)
            self.secondary_params = OrderedDict(self.default_secondary_params)
            self.all_params       = OrderedDict(self.default_all_params)
        elif key == 'primary':
            self.primary_params   = OrderedDict(self.default_primary_params)
            self.all_params.update(self.primary_params)
        elif key == 'secondary':
            self.secondary_params = OrderedDict(self.default_secondary_params)
            self.all_params.update(self.secondary_params)
        elif key in self.primary_params:
            self.primary_params[key] = self.default_primary_params[key]
            self.all_params[key]     = self.default_all_params[key]
        elif key in self.secondary_params:
            self.secondary_params[key] = self.default_secondary_params[key]
            self.all_params[key]       = self.default_all_params[key]
        else:
            err = '{} does not exist.'.format(GlaficParams.YELLOW_COLOR + key + GlaficParams.CLEAR_COLOR)
            GlaficParams.error(err)


class GlaficModels(object):
    GREEN_COLOR  = '\033[92m'
    YELLOW_COLOR = '\033[93m'
    RED_COLOR    = '\033[91m'
    CLEAR_COLOR  = '\033[0m'

    ERROR_CODE   = -1

    def __init__(self):
        # a bit wierd implementation...
        self.sets  = OrderedDict([('lens',   [[], 8, lensmodel.MODEL_LIST]),
                                  ('extend', [[], 9, extendmodel.MODEL_LIST]),
                                  ('point',  [[], 3, pointmodel.MODEL_LIST]),
                                  ('psf',    [[], 9, psfmodel.MODEL_LIST])])
    
    @classmethod
    def error(cls, err):
        print GlaficModels.RED_COLOR + 'Glaficmodels error: ' + GlaficModels.CLEAR_COLOR + err

    def __getitem__(self, key):
        if key in self.sets:
            return list(self.sets[key][0])
        else:
            err = '{} does not exist.'.format(GlaficModels.YELLOW_COLOR + key + GlaficModels.CLEAR_COLOR)
            GlaficModels.error(err)
            return None

    def _convert_params(self, key, params):
        try:
            if key in {'lens', 'extend'}:
                modelname = params.pop(0)
                params    = [float(_params) for _params in params]
            else:
                modelname = key
                params    = [float(_params) for _params in params]
        except ValueError:
            return modelname, None
        else:
            return modelname, params

    def _check_params(self, modelname, params):
        if params is None:
            return False
        else:
            return True

    def __setitem__(self, key, value):
        if not isinstance(value, list):
            raise GlaficError('Argument should be list.')

        if key in self.sets:
            self.sets[key][0] = value
        else:
            err = '{} does not exist'.format(GlaficModels.YELLOW_COLOR + key + GlaficModels.CLEAR_COLOR)
            GlaficModels.error(err)

    def reset(self, key):
        if key == 'all':
            self.sets['lens'][0]   = []
            self.sets['extend'][0] = []
            self.sets['point'][0]  = []
            self.sets['psf'][0]    = []
        elif key in self.sets:
            self.sets[key][0] = []
        else:
            err = '{} does not exist.'.format(GlaficModels.YELLOW_COLOR + key + GlaficModels.CLEAR_COLOR)
            GlaficModels.error(err)

    def append(self, key, params):
        if key not in self.sets:
            err = '{} does not exist.'.format(GlaficModels.YELLOW_COLOR + key + GlaficModels.CLEAR_COLOR)
            GlaficModels.error(err)
            return GlaficModels.ERROR_CODE
        if len(params) != self.sets[key][1]:
            GlaficModels.error('The number of arguments is bad.')
            return GlaficModels.ERROR_CODE

        modelname, params_t = self._convert_params(key, params)

        if not self._check_params(modelname, params_t):
            err = '{} is not suitable values for {}.'.format(params, GlaficModels.YELLOW_COLOR + modelname + GlaficModels.CLEAR_COLOR)
            GlaficModels.error(err)
            return GlaficModels.ERROR_CODE

        model = self.sets[key][2][modelname](*params_t)
        self.sets[key][0].append(model)


class Glafic(object):
    OUT_DIR = 'glean_out/'

    IMG_SUFFIX   = '_image.fits'
    SRC_SUFFIX   = '_source.fits'
    LENS_SUFFIX  = '_lens.fits'
    POINT_SUFFIX = '_point.dat'
    CRIT_SUFFIX  = '_crit.dat'
    OPT_SUFFIX   = '_optresult.dat'
    OPT_E_SUFFIX = '_optresult_extend.dat'
    OPT_P_SUFFIX = '_optresult_point.dat'

    KAPPA_INDEX  = 5
    GAMMA1_INDEX = 6
    GAMMA2_INDEX = 7
    GAMMA_INDEX  = 8
    MAG_INDEX    = 9
    XSRC_INDEX   = 11
    YSRC_INDEX   = 12

    N_IMG_INDEX = 0
    X_INDEX     = 2
    Y_INDEX     = 5

    path = None

    def __init__(self, inputname):
        self.inputname = Glafic.OUT_DIR + inputname
        self.params    = GlaficParams()
        self.models    = GlaficModels()

    def create_input(self):
        with open(self.inputname, 'w') as f:
            f.write('### primary parameters ###\n')
            for k, v in self.params['primary'].iteritems():
                f.write('{0:7}\t{1}\n'.format(k, v))
            f.write('\n')

            f.write('### secondary paramters ###\n')
            for k, v in self.params['secondary'].iteritems():
                f.write('{0:14}\t{1}\n'.format(k, v))
            f.write('\n')

            f.write('### startup ###\n')
            f.write('startup {0} {1} {2}\n'.format(len(self.models['lens']),
                                                   len(self.models['extend']),
                                                   len(self.models['point'])))
            f.write('\n')

            f.write('### lens model ###\n')
            for l in self.models['lens']:
                f.write(l.__str__())
            f.write('\n')

            f.write('### extended source model ###\n')
            for es in self.models['extend']:
                f.write(es.__str__())
            f.write('\n')

            f.write('### point source model ###\n')
            for ps in self.models['point']:
                f.write(ps.__str__())
            f.write('\n')

            f.write('### PSF model ###\n')
            for p in self.models['psf']:
                f.write(p.__str__())
            f.write('\n')

            f.write('end_startup\n')
            f.write('\n')

            f.write('### optimization ###\n')
            f.write('start_setopt\n')
            f.write('\n')

            f.write('### lens opt ###\n')
            for l in self.models['lens']:
                f.write(' '.join(map(str, l.opt.values())))
                f.write('\n')
            f.write('\n')

            f.write('### extended source opt ###\n')
            for es in self.models['extend']:
                f.write(' '.join(map(str, es.opt.values())))
                f.write('\n')
            f.write('\n')

            f.write('### point source opt ###\n')
            for ps in self.models['point']:
                f.write(' '.join(map(str, ps.opt.values())))
                f.write('\n')
            f.write('\n')

            f.write('### PSF opt ###\n')
            for p in self.models['psf']:
                f.write(' '.join(map(str, p.opt.values())))
                f.write('\n')
            f.write('\n')

            f.write('end_setopt\n')
            f.write('\n')

            f.write('### execute commands ###\n')
            f.write('start_command')

    def calcimage(self, redshift, ximg, yimg):
        proc     = Popen([self.path, self.inputname], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate('calcimage {0} {1} {2}\nquit'.format(redshift, ximg, yimg))

        kappa               = float(out.split('\n')[Glafic.KAPPA_INDEX].split()[2])
        gamma1              = float(out.split('\n')[Glafic.GAMMA1_INDEX].split()[2])
        gamma2              = float(out.split('\n')[Glafic.GAMMA2_INDEX].split()[2])
        gamma               = float(out.split('\n')[Glafic.GAMMA_INDEX].split()[2])
        if gamma2 / gamma >= 0:
            phi = 1. / 2 * np.arccos(gamma1 / gamma)
        else:
            phi = -1. / 2 * np.arccos(gamma1 / gamma)
        mag                 = np.abs(float(out.split('\n')[Glafic.MAG_INDEX].split()[2]))
        xsrc                = float(out.split('\n')[Glafic.XSRC_INDEX].split()[2])
        ysrc                = float(out.split('\n')[Glafic.YSRC_INDEX].split()[2])
        srcinfo             = {'kappa':kappa, 'gamma1':gamma1, 'gamma2':gamma2, 'gamma':gamma,
                               'phi':phi, 'mag':mag, 'xsrc':xsrc, 'ysrc':ysrc}

        return srcinfo

    def findimg(self):
        proc     = Popen([Glafic.path, self.inputname], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        out, err = proc.communicate('findimg\nquit')

        n_img  = int(out.split('\n')[Glafic.N_IMG_INDEX].split()[2])
        x, y = [], []
        for i in xrange(n_img):
            x.append(float(out.split('\n')[Glafic.N_IMG_INDEX + i + 1].split()[Glafic.X_INDEX]))
            y.append(float(out.split('\n')[Glafic.N_IMG_INDEX + i + 1].split()[Glafic.Y_INDEX]))
        imginfo = {'n_img':n_img, 'x':x, 'y':y}

        return imginfo

    def writeimage(self, params):
        proc = Popen([Glafic.path, self.inputname], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate('writeimage {0} {1}\nquit'.format(*params))

    def writeimage_ori(self, params):
        proc = Popen([Glafic.path, self.inputname], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate('writeimage_ori {0} {1}\nquit'.format(*params))

    def writelens(self, params):
        proc = Popen([Glafic.path, self.inputname], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate('writelens {0}\nquit'.format(*params))

    def writecrit(self, params):
        proc = Popen([Glafic.path, self.inputname], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate('writecrit {0}\nquit'.format(*params))

    def optimize_p(self, params):
        proc = Popen([Glafic.path, self.inputname], stdin=PIPE, stdout=PIPE, stderr=PIPE)
        proc.communicate('readobs_point {}\nparprior {}\noptpoint\nquit'.format(*params))

    def readopt_e(self):
        optname = self.params['prefix'] + Glafic.OPT_E_SUFFIX
        with open(optname, 'r') as f:
            data = f.readlines()
            chi2 = float(data[3].split()[2])
            tx   = float(data[-3].split()[4])
            ty   = float(data[-3].split()[5])

        return tx, ty, chi2

    def readopt_p(self):
        optname = self.params['prefix'] + Glafic.OPT_P_SUFFIX
        with open(optname, 'r') as f:
            data = f.readlines()
            chi2 = float(data[3].split()[2])
            tx   = float(data[-2].split()[2])
            ty   = float(data[-2].split()[3])

        return tx, ty, chi2
