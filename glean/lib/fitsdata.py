# coding:UTF-8

import sys
import numpy as np
from astropy.io import fits

from copy import deepcopy

import beammodel
reload(beammodel)


def gauss(x, m, s):
    return 1 / (np.sqrt(2*np.pi) * s) * np.exp(-(x - m)**2 / (2 * s**2))


class FITSDataError(Exception):
    def __init__(self, message):
        self.message = message

    def __str__(self):
        return self.message


class FITSData(object):
    def __init__(self, data, header, check=False):
        self.data   = data
        self.header = header
        if check:
            self.check_header()

    @classmethod
    def initbyname(cls, fitsname, mode=2, check=False):
        """
        mode: 0 -> make data whose elements are all 0 with the same shape as fitsname
        mode: 1 -> make data whose elements are all 1 with the same shape as fitsname
        mode: 2 -> make data whose elements are the same as fitsname
        """
        data, header = fits.getdata(fitsname, header=True)
        if mode == 0:
            data = np.zeros_like(data)
        elif mode == 1:
            data = np.ones_like(data)

        return cls(data, header, check)

    @classmethod
    def initbydata(cls, data, header, check=False):
        if isinstance(header, dict):
            header = fits.Header(header.items())
        elif isinstance(header, fits.Header):
            pass
        else:
            raise FITSDataError('Header should be dictionary or astropy.io.fits.Header.')

        if not isinstance(data, np.ndarray):
            raise FITSDataError('Data should be numpy.ndarray.')

        return cls(data, header, check)

    @classmethod
    def initbyshape(cls, shape, mode=0):
        if mode == 0:
            data   = np.zeros(shape)
            header = fits.Header()
        elif mode == 1:
            data   = np.ones(shape)
            header = fits.Header()

        return cls(data, header)

    @classmethod
    def check_dimension(cls, fitsname):
        data = fits.getdata(fitsname)
        dim  = data.ndim

        return dim

    def __neg__(self):
        data   = -self.data
        header = self.header

        return self.__class__.initbydata(data, header)

    def __add__(self, obj):
        """ addition is not commutative! """
        if isinstance(obj, (int, float)):
            data   = self.data + obj
            header = self.header
        elif isinstance(obj, FITSData):
            data   = self.data + obj.data
            header = self.header
        else:
            raise FITSDataError('These two arguments cannot be added.')

        return self.__class__.initbydata(data, header)

    def __sub__(self, obj):
        """ subtraction is not commutative! """
        return self.__add__(-obj)

    def __mul__(self, obj):
        """ multiplication is not commutative! """
        if isinstance(obj, (int, float)):
            data   = self.data * obj
            header = self.header
        elif isinstance(obj, FITSData):
            data   = self.data * obj.data
            header = self.header
        else:
            raise FITSDataError('These two arguments cannot be multiplied.')

        return self.__class__.initbydata(data, header)

    def check_header(self):
        if 'BMAJ' not in self.header:
            print 'FITS header does not have a keyword of "BMAJ".'
            bmaj = float(raw_input('BMAJ (deg): '))
            self.append_header({'BMAJ': bmaj})
        if 'BMIN' not in self.header:
            print 'FITS header does not have a keyword of "BMIN".'
            bmin = float(raw_input('BMIN (deg): '))
            self.append_header({'BMIN': bmin})
        if 'BPA' not in self.header:
            print 'FITS header does not have a keyword of "BPA".'
            Bpa = float(raw_input('BPA (deg): '))
            self.append_header({'BPA': bpa})
        if 'REDSHIFT' not in self.header:
            print 'FITS header does not have a keyword of "REDSHIFT".'
            redshift = float(raw_input('REDSHIFT: '))
            self.append_header({'REDSHIFT': redshift})

    def set_header(self, header):
        if isinstance(header, dict):
            self.header = fits.Header(header.items())
        elif isinstance(header, fits.Header):
            self.header = header
        else:
            raise FITSDataError('Header should be dictionary or astropy.io.fits.Header.')

    def append_header(self, header):
        if isinstance(header, (dict, fits.Header)):
            self.header.update(header)
        else:
            raise FITSDataError('Header should be dictionary or astropy.io.fits.Header.')

    def write_fits(self, fitsname, clobber=True):
        fits.writeto(fitsname, self.data, self.header, clobber=clobber)


class FITSData2D(FITSData):
    def __init__(self, data, header, check=False):
        super(self.__class__, self).__init__(data, header, check)
        if not self.data.ndim == 2:
            raise FITSDataError('This FITS data is not 2D.')

    def extendto3D(self):
        data   = np.expand_dims(self.data, axis=0)
        header = self.header

        return FITSData3D(data, header)

    def abs(self, mode='in-place'):
        if mode == 'in-place':
            self.data = np.abs(self.data)

            return self
        elif mode == 'copy':
            data   = np.abs(self.data)
            header = self.header

            return self.__class__(data, header)
        
    def findmax(self, maskcls=None):
        if maskcls is None:
            maskedcls = self
        else:
            maskedcls = self * maskcls
        maskedcls.data = np.ma.masked_equal(maskedcls.data, 0, copy=False)
        
        ind_max = np.unravel_index(maskedcls.data.argmax(), maskedcls.data.shape)
        sb_max  = maskedcls.data[ind_max]

        try:
            ind_up    = ind_max[0] + 1, ind_max[1]
            sb_up     = self.data[ind_up]
            ind_down  = ind_max[0] - 1, ind_max[1]
            sb_down   = self.data[ind_down]
            ind_left  = ind_max[0], ind_max[1] - 1
            sb_left   = self.data[ind_left]
            ind_right = ind_max[0], ind_max[1] + 1
            sb_right  = self.data[ind_right]
        except IndexError:
            raise FITSDataError('Findmax error.')

        ind_cog = ((ind_max[0] * sb_max + ind_up[0] * sb_up + ind_down[0] * sb_down) / (sb_max + sb_up + sb_down),
                   (ind_max[1] * sb_max + ind_right[1] * sb_right + ind_left[1] * sb_left) / (sb_max + sb_right + sb_left))
        pos_x = (ind_cog[1] + 1 - self.header['CRPIX1']) * self.header['CDELT1'] + self.header['CRVAL1']
        pos_y = (ind_cog[0] + 1 - self.header['CRPIX2']) * self.header['CDELT2'] + self.header['CRVAL2']
        
        return sb_max, (pos_x, pos_y)

    # def findnthmax(self, maskcls=None, n=2):
    #     if maskcls is None:
    #         maskedcls = self
    #     else:
    #         maskedcls = self * maskcls
    #     maskedcls.data = np.ma.masked_equal(maskedcls.data, 0, copy=False)

    #     for i in xrange(n):
    #         ind_max = np.unravel_index(maskedcls.data.argmax(), maskedcls.data.shape)
    #         sb_max  = maskedcls.data[ind_max]

    #         maskedcls.data[ind_max] = 0

    #     try:
    #         ind_up    = ind_max[0] + 1, ind_max[1]
    #         sb_up     = self.data[ind_up]
    #         ind_down  = ind_max[0] - 1, ind_max[1]
    #         sb_down   = self.data[ind_down]
    #         ind_left  = ind_max[0], ind_max[1] - 1
    #         sb_left   = self.data[ind_left]
    #         ind_right = ind_max[0], ind_max[1] + 1
    #         sb_right  = self.data[ind_right]
    #     except IndexError:
    #         raise FITSDataError('Findmax error.')

    #     ind_cog = ((ind_max[0] * sb_max + ind_up[0] * sb_up + ind_down[0] * sb_down) / (sb_max + sb_up + sb_down),
    #                (ind_max[1] * sb_max + ind_right[1] * sb_right + ind_left[1] * sb_left) / (sb_max + sb_right + sb_left))
    #     pos_x = (ind_cog[1] + 1 - self.header['CRPIX1']) * self.header['CDELT1'] + self.header['CRVAL1']
    #     pos_y = (ind_cog[0] + 1 - self.header['CRPIX2']) * self.header['CDELT2'] + self.header['CRVAL2']
        
    #     return sb_max, (pos_x, pos_y)

    def findmultmax(self, xs, ys, rx, ry, pa):
        data   = np.zeros_like(self.data)
        header = self.header

        testcls = deepcopy(self)
        testcls *= 0
        
        sy, sx = data.shape
        result = []
        i = 0
        for _xs, _ys, _rx, _ry, _pa in zip(xs, ys, rx, ry, pa):
            def solve(x0, y0, a, b, theta, mode, v):
                if mode == 'x':
                    A = np.sin(theta)**2 / a**2 + np.cos(theta)**2 / b**2
                    B = (2 * (v * np.cos(theta) - x0 * np.cos(theta) - y0 * np.sin(theta)) * np.sin(theta) / a**2 - \
                         2 * (v * np.sin(theta) - x0 * np.sin(theta) + y0 * np.cos(theta)) * np.cos(theta) / b**2)
                    C = (v * np.cos(theta) - x0 * np.cos(theta) - y0 * np.sin(theta))**2 / a**2 + \
                        (v * np.sin(theta) - x0 * np.sin(theta) + y0 * np.cos(theta))**2 / b**2 - 1
                elif mode == 'y':
                    A = np.cos(theta)**2 / a**2 + np.sin(theta)**2 / b**2
                    B = (2 * (v * np.sin(theta) - y0 * np.sin(theta) - x0 * np.cos(theta)) * np.cos(theta) / a**2 - \
                         2 * (v * np.cos(theta) - y0 * np.cos(theta) + x0 * np.sin(theta)) * np.sin(theta) / b**2)
                    C = (v * np.sin(theta) - y0 * np.sin(theta) - x0 * np.cos(theta))**2 / a**2 + \
                        (v * np.cos(theta) - y0 * np.cos(theta) + x0 * np.sin(theta))**2 / b**2 - 1

                if B**2 - 4*A*C >= 0:
                    result = (-B - np.sqrt(B**2 - 4*A*C)) / (2 * A), (-B + np.sqrt(B**2 - 4*A*C)) / (2 * A)
                else:
                    result = None, None

                return result

            data *= 0
            for px_x in xrange(2, sx):
                coord_x = (px_x - 0.5 - header['CRPIX1']) * header['CDELT1']
                coord_ymin, coord_ymax = solve(_xs, _ys, _rx, _ry, _pa, 'x', coord_x)
                if coord_ymin is None:
                    continue
                px_ymin, px_ymax = int(np.round(coord_ymin / header['CDELT2'] + header['CRPIX2'])), \
                                   int(np.round(coord_ymax / header['CDELT2'] + header['CRPIX2']))
                data[px_ymin-1:px_ymax, px_x-2:px_x] = 1
            for px_y in xrange(2, sy):
                coord_y = (px_y - 0.5 - header['CRPIX2']) * header['CDELT2']
                coord_xmin, coord_xmax = solve(_xs, _ys, _rx, _ry, _pa, 'y', coord_y)
                if coord_xmin is None:
                    continue
                px_xmin, px_xmax = int(np.round(coord_xmin / header['CDELT1'] + header['CRPIX1'])), \
                                   int(np.round(coord_xmax / header['CDELT1'] + header['CRPIX1']))
                data[px_y-2:px_y, px_xmin-1:px_xmax] = 1
            if len(np.where(data == 1)[0]) == 0:
                px_x, px_y = int(np.round(_xs / header['CDELT1'] + header['CRPIX1'])), \
                             int(np.round(_ys / header['CDELT2'] + header['CRPIX2']))
                data[px_y-1, px_x-1] = 1

            maskcls  = self.__class__.initbydata(data, header)

            testcls += maskcls
            
            maskcls.write_fits('glean_out/mask_mult_{}.fits'.format(i + 1))
            result.append(self.findmax(maskcls))

            i += 1

        testcls.write_fits('glean_out/mask_mult.fits')
        return result


class FITSData3D(FITSData):
    def __init__(self, data, header, check=False):
        super(self.__class__, self).__init__(data, header, check)
        if not self.data.ndim == 3:
            raise FITSDataError('This FITS data is not 3D.')
        self._i = 0

    ##### is this needed??? #####
    # def __mul__(self, obj):
    #     if isinstance(obj, (int, float)):
    #         data   = self.data * obj
    #         header = self.header
    #     elif isinstance(obj, (FITSData2D, FITSData3D)):
    #         data   = self.data * obj.data
    #         header = self.header
    #     else:
    #         raise FITSDataError('These two arguments cannot be multiplied.')

    #     return self.__class__.initbydata(data, header)

    def __iter__(self):
        return self

    def next(self):
        if self._i == self.data.shape[0]:
            self._i = 0
            raise StopIteration()
        subdata   = self.data[self._i]
        subheader = self.header
        sub       = FITSData2D.initbydata(subdata, subheader)
        self._i  += 1

        return sub

    def append_data(self, data):
        if isinstance(data, np.ndarray):
            self.data = np.append(self.data, np.expand_dims(data, axis=0), axis=0)
        elif isinstance(data, FITSData2D):
            self.data = np.append(self.data, np.expand_dims(data.data, axis=0), axis=0)
        else:
            raise FITSDataError('Appended data should be numpy.ndarray or fitsdata.FITSData2D.')
