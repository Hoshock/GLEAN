# coding:UTF-8

##
## Author: Tsuyoshi ISHIDA
##
## Affiliation: Dept. of Astronomy, Fac. of Science, Univ. of Tokyo
##
## Contact: tishida@ioa.s.u-tokyo.ac.jp
##
## Date: 2015/10/26
##

##### import modulus #####
from __future__ import division, absolute_import
import sys

from .lib import interpreter
reload(interpreter)
from .lib import glean as gl
reload(gl)
from .lib.glafic import glafic as gf
reload(gf)
from .lib import fitsdata
reload(fitsdata)


##### define classes #####
class MainError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


def main():
    argv = sys.argv
    argc = len(argv)
    if argc >= 3:
        glafic_path = argv[1]
        fitsname    = argv[2]
        maskname    = argv[3:]
    else:
        raise MainError('The number of arguments is bad.')

    # check the dimension of FITS
    fits_dim = fitsdata.FITSData.check_dimension(fitsname)
    if fits_dim == 2:
        fitscls2d = fitsdata.FITSData2D.initbyname(fitsname, check=True)
        fitscls   = fitscls2d.extendto3D()
    elif fits_dim == 3:
        fitscls   = fitsdata.FITSData3D.initbyname(fitsname, check=True)
    else:
        raise MainError('FITS data should be 2D or 3D.')

    if len(maskname) == 0:
        maskcls = None
    else:
        mask_dim = fitsdata.FITSData.check_dimension(maskname[0])
        if mask_dim == 2:
            maskcls = fitsdata.FITSData2D.initbyname(maskname[0])
            for submask in maskname:
                maskcls *= fitsdata.FITSData2D.initbyname(submask)
        # elif fitsdata.FITSData.check_dimension(maskname[0]) == 3:
        #     maskcls = fitsdata.FITSData3D.initbyname(maskname[0])
        #     for _maskname in maskname:
        #         maskcls *= fitsdata.FITSData3D.initbyname(_maskname)
        else:
            raise MainError('Mask data should be 2D.')

    if maskcls is not None:
        maskcls.write_fits(gl.Glean.OUT_DIR + 'mask.fits')
        if fitscls.data[0].shape != maskcls.data.shape:
            raise MainError('Image sizes of data and mask should be the same.')

    gf.Glafic.path = glafic_path
    glafic_i       = gf.Glafic('one_image.input')
    glafic_s       = gf.Glafic('one_source.input')
    glean          = gl.Glean(glafic_i, glafic_s, fitscls, maskcls)

    Interpreter = interpreter.Interpreter(glafic_i, glafic_s, glean)
    Interpreter.start()

##### main #####
if __name__ == '__main__':
    # run main.py (glafic path) (fitsname [2D/3D]) (maskname [optional])
    main()
