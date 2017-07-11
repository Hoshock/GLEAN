# coding:UTF-8

import os
import glob
import numpy as np
from collections import OrderedDict
from copy import deepcopy

from .glafic import glafic as gf
reload(gf)
from .glafic import extendmodel
reload(extendmodel)
from .glafic import pointmodel
reload(pointmodel)
import fitsdata
reload(fitsdata)
import beammodel
reload(beammodel)


class GleanError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class GleanParams(object):
    GREEN_COLOR  = '\033[92m'
    YELLOW_COLOR = '\033[93m'
    RED_COLOR    = '\033[91m'
    CLEAR_COLOR  = '\033[0m'

    ERROR_CODE   = -1

    def __init__(self):
        self.default_all_params = OrderedDict([('gain', 0.1), ('threshold', 3e-4),
                                               ('limit', 50), ('zmin', 0), ('zmax', -1), ('imgstep', 10),
                                               ('resstep', 10), ('sigma', 3e-3), ('flag_sconv', 1),
                                               ('flag_iconv', 1), ('uncertainty', 0.005)])
        self.all_params         = OrderedDict(self.default_all_params)

    @classmethod
    def error(cls, err):
        print GleanParams.RED_COLOR + 'Gleanparams error: ' + GleanParams.CLEAR_COLOR + err
        
    def __getitem__(self, key):
        if key == 'all':
            return OrderedDict(self.all_params)
        elif key in self.all_params:
            return self.all_params[key]
        else:
            err = '{} does not exist.'.format(GleanParams.YELLOW_COLOR + key + GleanParams.CLEAR_COLOR)
            GleanParams.error(err)
            return None

    def _convert_params(self, key, value):
        try:
            if isinstance(self.all_params[key], int):
                return int(value)
            elif isinstance(self.all_params[key], float):
                return float(value)
        except ValueError:
            return None

    def _check_params(self, key, value):
        if key in {'gain', }:
            return 0 < value <= 1
        elif key in {'threshold', 'resstep', 'imgstep', 'sigma', 'uncertainty'}:
            return 0 < value
        elif key in {'limit', 'zmax'}:
            return -1 <= value
        elif key in {'zmin', 'flag_sconv', 'flag_iconv'}:
            return 0 <= value

    def __setitem__(self, key, value):
        if key not in self.all_params:
            err = '{} does not exist.'.format(GleanParams.YELLOW_COLOR + key + GleanParams.CLEAR_COLOR)
            GleanParams.error(err)
            return GleanParams.ERROR_CODE

        value_t = self._convert_params(key, value)
        if self._check_params(key, value_t):
            self.all_params[key] = value_t
        else:
            err = '{} is not a suitable value for {}.'.format(value, GleanParams.YELLOW_COLOR + key + GleanParams.CLEAR_COLOR)
            GleanParams.error(err)

    def reset(self, key):
        if key == 'all':
            self.all_params = OrderedDict(self.default_all_params)
        elif key in self.all_params:
            self.all_params[key] = self.default_all_params[key]
        else:
            err = '{} does not exist.'.format(GleanParams.YELLOW_COLOR + key + GleanParams.CLEAR_COLOR)
            GleanParams.error(err)


class Glean(object):
    OUT_DIR = 'glean_out/'

    GREEN_COLOR  = '\033[92m'
    YELLOW_COLOR = '\033[93m'
    RED_COLOR    = '\033[91m'
    CLEAR_COLOR  = '\033[0m'

    # PRIOR_NAME    = OUT_DIR + 'prior.dat'
    # MULT_NAME     = OUT_DIR + 'mult.dat'

    ERROR_CODE   = -1

    def __init__(self, glafic_i, glafic_s, fitscls, maskcls):
        self.params            = GleanParams()
        self.glafic_i          = glafic_i
        self.glafic_s          = glafic_s
        self.default_fitscls   = fitscls
        self.maskcls           = maskcls
        self.beam              = beammodel.Gauss2D(self.default_fitscls.header['BMAJ'], self.default_fitscls.header['BMIN'],
                                                   self.default_fitscls.header['BPA'], self.default_fitscls.header['CDELT1'],
                                                   self.default_fitscls.header['CDELT2'], mode='image')

        # once FITS is loaded, these parameters sholud not be changed
        self.glafic_i.params['xmin']    = (0.5 - self.default_fitscls.header['CRPIX1']) * self.default_fitscls.header['CDELT1']
        self.glafic_i.params['xmax']    = (self.default_fitscls.header['NAXIS1'] + 0.5
                                           - self.default_fitscls.header['CRPIX1']) * self.default_fitscls.header['CDELT1']
        self.glafic_i.params['ymin']    = (0.5 - self.default_fitscls.header['CRPIX2']) * self.default_fitscls.header['CDELT2']
        self.glafic_i.params['ymax']    = (self.default_fitscls.header['NAXIS2'] + 0.5
                                           - self.default_fitscls.header['CRPIX2']) * self.default_fitscls.header['CDELT2']
        self.glafic_i.params['pix_ext'] = self.default_fitscls.header['CDELT1']

    @classmethod
    def success(self, msg):
        print Glean.GREEN_COLOR + 'Success: ' + Glean.CLEAR_COLOR + msg

    @classmethod
    def error(self, err):
        print Glean.RED_COLOR + 'Glean error: ' + Glean.CLEAR_COLOR + err

    def execute(self, phase=1):
        prefix_i = self.glafic_i.params['prefix']
        prefix_s = self.glafic_s.params['prefix']
        
        self.all_img_name  = prefix_i + '_image_all.fits'
        self.all_src_name  = prefix_s + '_source_all.fits'
        self.all_res_name  = prefix_i + '_residue_{}.fits'
        self.one_imgs_name = prefix_i + '_image_indiv_{}.fits'
        self.one_srcs_name = prefix_s + '_source_indiv_{}.fits'
        self.reg_name      = prefix_i + '_mutliple_images_{}.reg'
        
        if glob.glob(self.all_img_name) or glob.glob(self.all_src_name) or \
           glob.glob(self.all_res_name) or glob.glob(self.one_imgs_name.replace('{}', '*')) or \
           glob.glob(self.one_srcs_name.replace('{}', '*')) or glob.glob(self.reg_name.replace('{}', '*')):
            check = raw_input('Output files already exist. Continue? (y/[n]): ')
            if check == 'y':
                pass
            else:
                return

        self.glafic_i.create_input()
        self.fitscls = deepcopy(self.default_fitscls)

        zsrc = self.default_fitscls.header['REDSHIFT']
        
        xmin_i    = self.glafic_i.params['xmin']
        ymin_i    = self.glafic_i.params['ymin']
        xmax_i    = self.glafic_i.params['xmax']
        ymax_i    = self.glafic_i.params['ymax']
        pix_ext_i = self.glafic_i.params['pix_ext']

        xmin_s    = self.glafic_s.params['xmin']
        ymin_s    = self.glafic_s.params['ymin']
        xmax_s    = self.glafic_s.params['xmax']
        ymax_s    = self.glafic_s.params['ymax']
        pix_ext_s = self.glafic_s.params['pix_ext']

        one_img_name     = prefix_i + gf.Glafic.IMG_SUFFIX
        one_src_name     = prefix_s + gf.Glafic.SRC_SUFFIX
        one_img_inp_name = self.glafic_i.inputname
        one_src_inp_name = self.glafic_s.inputname
        one_point_name   = prefix_i + gf.Glafic.POINT_SUFFIX

        threshold   = self.params['threshold']
        gain        = self.params['gain']
        resstep     = self.params['resstep']
        imgstep     = self.params['imgstep']
        limit       = self.params['limit']
        sigma       = self.params['sigma']
        zmin        = self.params['zmin']
        zmax        = self.params['zmax']
        flag_sconv  = self.params['flag_sconv']
        flag_iconv  = self.params['flag_iconv']
        uncertainty = self.params['uncertainty']

        shape_i = (int(round((ymax_i - ymin_i) / pix_ext_i)), int(round((xmax_i - xmin_i) / pix_ext_i)))
        shape_s = (int(round((ymax_s - ymin_s) / pix_ext_s)), int(round((xmax_s - xmin_s) / pix_ext_s)))
        
        self.all_img  = fitsdata.FITSData3D.initbyshape((0, shape_i[0], shape_i[1]))
        self.all_src  = fitsdata.FITSData3D.initbyshape((0, shape_s[0], shape_s[1]))
        for j, self.fitscls_p in enumerate(self.fitscls):
            if j < zmin:
                continue
            if zmax != -1 and zmax < j:
                continue
            
            regfile = open(self.reg_name.format(j + 1), 'w')
            regfile.write('# Region file format: DS9 version 4.1\n')
            regfile.write('global color=red dashlist=8 3 width=1 font="helvetica 10 normal roman" select=1 highlite=1 dash=0 fixed=0 edit=1 move=1 delete=1 include=1 source=1\n')
            regfile.write('wcs;\n')

            self.all_img_p = fitsdata.FITSData2D.initbyshape(shape_i)
            self.all_src_p = fitsdata.FITSData2D.initbyshape(shape_s)
            self.all_res   = fitsdata.FITSData3D.initbyshape((0, shape_i[0], shape_i[1]))
            self.all_res_p = fitsdata.FITSData2D.initbyshape(shape_i)
            self.one_img   = fitsdata.FITSData2D.initbyshape(shape_i)
            self.one_src   = fitsdata.FITSData2D.initbyshape(shape_s)
            self.one_imgs  = fitsdata.FITSData3D.initbyshape((0, shape_i[0], shape_i[1]))
            self.one_srcs  = fitsdata.FITSData3D.initbyshape((0, shape_s[0], shape_s[1]))
            
            i = 0
            sb_max_prev, pos_prev = None, None
            try:
                while True:
                    sb_max, pos = self.fitscls_p.findmax(self.maskcls)
                    if sb_max == sb_max_prev and pos == pos_prev:
                        Glean.error('Iteration error.')
                        break
                    if sb_max <= threshold:
                        Glean.success('Residual max reaches the threshold.')
                        break
                    print '#{}_{}'.format(j + 1, i + 1)
                    print '{:<25} = {}'.format(Glean.YELLOW_COLOR + 'residual max' + Glean.CLEAR_COLOR, sb_max)
                    print '{:<25} = {}'.format(Glean.YELLOW_COLOR + 'image position' + Glean.CLEAR_COLOR, pos)

                    srcinfo = self.glafic_i.calcimage(zsrc, *pos)
                    xsrc    = srcinfo['xsrc']
                    ysrc    = srcinfo['ysrc']
                    kappa   = srcinfo['kappa']
                    gamma   = srcinfo['gamma']
                    phi     = srcinfo['phi']
                    mag     = srcinfo['mag']
                    sbsrc   = 1.
                    print '{:<25} = {}'.format(Glean.YELLOW_COLOR + 'phi' + Glean.CLEAR_COLOR, phi)
                    print '{:<25} = {}'.format(Glean.YELLOW_COLOR + 'kappa' + Glean.CLEAR_COLOR, kappa)
                    print '{:<25} = {}'.format(Glean.YELLOW_COLOR + 'gamma' + Glean.CLEAR_COLOR, gamma)
                    print '{:<25} = {}'.format(Glean.YELLOW_COLOR + 'magnification' + Glean.CLEAR_COLOR, mag)
                    print '{:<25} = ({}, {})'.format(Glean.YELLOW_COLOR + 'source position' + Glean.CLEAR_COLOR, xsrc, ysrc)
                
                    gauss = extendmodel.Gauss(zsrc, sbsrc, xsrc, ysrc, 0, 0, sigma, 0)
                    point = pointmodel.Point(zsrc, xsrc, ysrc)
                    self.glafic_i.models['extend'] = [gauss]
                    self.glafic_i.models['point']  = [point]
                    self.glafic_i.create_input()

                    imginfo = self.glafic_i.findimg()
                    n_img   = imginfo['n_img']
                    x       = imginfo['x']
                    y       = imginfo['y']

                    ### phase-II reconstruction ###
                    # if phase == 2:
                    #     rx = []
                    #     ry = []
                    #     pa = []
                    #     for n in xrange(n_img):
                    #         _srcinfo = self.glafic_i.calcimage(zsrc, x[n], y[n])
                    #         _kappa   = _srcinfo['kappa']
                    #         _gamma   = _srcinfo['gamma']
                    #         _phi     = _srcinfo['phi']
                    #         _mag     = _srcinfo['mag']
                    
                    #         _uncertainty = beammodel.Gauss2D(uncertainty / 3600, uncertainty / 3600, 0, pix_ext_s, pix_ext_s, mode='source')
                    #         _uncertainty.calcbeam_i(pix_ext_i, pix_ext_i, _kappa, _gamma, _phi)
                    #         rx.append(_uncertainty.a2)
                    #         ry.append(_uncertainty.b2)
                    #         pa.append(_uncertainty.theta)

                    #     multinfo = self.fitscls_p.findmultmax(x, y, rx, ry, pa)
                    #     multfile = open(Glean.MULT_NAME, 'w')
                    #     multfile.write('{} {} {} {}\n'.format(1, n_img, zsrc, 0))
                    #     for info in multinfo:
                    #         multfile.write('{} {} {} {} {} {} {} {}\n'.format(info[1][0], info[1][1], info[0], uncertainty / 2.35, 0, 0, 0, 0))
                    #     multfile.close()
                    
                    #     priorfile = open(Glean.PRIOR_NAME, 'w')
                    #     # priorfile.write('gauss point 1 2 {} {}\n'.format(xsrc, uncertainty / 2.35))
                    #     # priorfile.write('gauss point 1 3 {} {}\n'.format(ysrc, uncertainty / 2.35))
                    #     priorfile.close()

                    #     self.glafic_i.optimize_p((Glean.MULT_NAME, Glean.PRIOR_NAME))
                    #     tx, ty, chi2 = self.glafic_i.readopt_p()
                    
                    #     print '{:<25} = {}'.format(Glean.YELLOW_COLOR + 'chi^2' + Glean.CLEAR_COLOR, chi2)
                    
                    #     gauss = extendmodel.Gauss(zsrc, sbsrc, tx, ty, 0, 0, sigma, 0)
                    #     point = pointmodel.Point(zsrc, tx, ty)
                    #     self.glafic_i.models['extend'] = [gauss]
                    #     self.glafic_i.models['point']  = [point]
                    #     self.glafic_i.create_input()
                    
                    #     imginfo = self.glafic_i.findimg()
                    #     n_img   = imginfo['n_img']
                    #     x       = imginfo['x']
                    #     y       = imginfo['y']

                    print '===> output modeled image plane'
                    self.glafic_i.writeimage([0, 0])
                    for n in xrange(n_img):
                        regfile.write('text({0},{1}) # text={{{2}}}\n'.format(x[n], y[n], i + 1))

                    self.glafic_s.models['extend'] = [gauss]
                    self.glafic_s.models['point']  = [point]
                    self.glafic_s.create_input()

                    print '===> output modeled source plane'
                    self.glafic_s.writeimage_ori([0, 0])

                    self.one_img = fitsdata.FITSData2D.initbyname(one_img_name)
                    if flag_iconv != 0:
                        print '===> convolve modeled image plane'
                        self.beam.convolve(self.one_img, 'image')  # it may need to be revised
                        self.conv_i = sb_max / self.one_img.data.max()
                        self.one_img *= self.conv_i * gain

                    self.one_src = fitsdata.FITSData2D.initbyname(one_src_name)
                    if phase == 1:
                        self.beam.calcbeam_s(pix_ext_s, pix_ext_s, kappa, gamma, phi)
                        if flag_sconv != 0:
                            print '===> convolve modeled source plane'
                            self.beam.convolve(self.one_src, 'source')
                            self.conv_s = self.conv_i * gain
                            self.one_src *= self.conv_s

                    self.all_img_p = self.one_img + self.all_img_p	# it may need to be revised
                    self.all_src_p = self.one_src + self.all_src_p	# it may need to be revised
                    self.all_res_p = self.fitscls_p - self.one_img

                    if i % resstep == 0:
                        self.all_res.append_data(self.all_res_p)
                    if i % imgstep == 0:
                        self.one_imgs.append_data(self.one_img)
                        self.one_srcs.append_data(self.one_src)

                    self.fitscls_p = self.all_res_p
                    sb_max_prev, pos_prev = sb_max, pos

                    i += 1
                    print ''
                    if i == limit:
                        Glean.success('The number of iteration reaches the limit.')
                        break
            
                regfile.close()
                self.all_img.append_data(self.all_img_p)
                self.all_src.append_data(self.all_src_p)
                self.all_res.append_data(self.all_res_p)
                self.all_res.set_header(self.all_img_p.header)
                self.all_res.write_fits(self.all_res_name.format(j+1))
                self.one_imgs.append_data(self.one_img)
                self.one_imgs.set_header(self.all_img_p.header)
                self.one_imgs.write_fits(self.one_imgs_name.format(j+1))
                self.one_srcs.append_data(self.one_src)
                self.one_srcs.set_header(self.all_src_p.header)
                self.one_srcs.write_fits(self.one_srcs_name.format(j+1))
                print ''

            # This will not kill glafic, so it should be revised in future
            except KeyboardInterrupt:
                print '\n'
                print Glean.error('Keyboard Interrupted')
                print Glean.success('Output current results')

                regfile.close()
                self.all_img.append_data(self.all_img_p)
                self.all_src.append_data(self.all_src_p)
                self.all_res.append_data(self.all_res_p)
                self.all_res.set_header(self.all_img_p.header)
                self.all_res.write_fits(self.all_res_name.format(j+1))
                self.one_imgs.append_data(self.one_img)
                self.one_imgs.set_header(self.all_img_p.header)
                self.one_imgs.write_fits(self.one_imgs_name.format(j+1))
                self.one_srcs.append_data(self.one_src)
                self.one_srcs.set_header(self.all_src_p.header)
                self.one_srcs.write_fits(self.one_srcs_name.format(j+1))
                print ''
                
                break

        self.all_img.set_header(self.all_img_p.header)
        self.all_img.write_fits(self.all_img_name)
        self.all_src.set_header(self.all_src_p.header)
        self.all_src.write_fits(self.all_src_name)

        # delete all intermediate files
        os.system('rm -f {}'.format(one_img_name))
        os.system('rm -f {}'.format(one_src_name))
        os.system('rm -f {}'.format(one_img_inp_name))
        os.system('rm -f {}'.format(one_src_inp_name))
        os.system('rm -f {}'.format(one_point_name))
