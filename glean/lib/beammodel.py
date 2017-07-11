# coding:UTF-8

import numpy as np
# import matplotlib.pyplot as plt
# plt.style.use('ggplot')
# from mpl_toolkits.mplot3d import Axes3D
from astropy.convolution import convolve as _convolve

def gauss(x, m, s):
    return 1 / (np.sqrt(2*np.pi) * s) * np.exp(-(x - m)**2 / (2 * s**2))

def toodd(i):
    if int(i) % 2 == 0:
        return int(i) + 1
    else:
        return int(i)

class Gauss2D(object):
    def __init__(self, bmaj, bmin, bpa, dx, dy, mode):
        if mode == 'image':
            self.bmaj_i          = bmaj * 3600
            self.bmin_i          = bmin * 3600
            self.bpa_i           = bpa * np.pi / 180
            self.dx_i, self.dy_i = dx, dy
            self.xsize_i         = toodd(self.bmaj_i / self.dx_i * 2)  # 2 * FWHM
            self.ysize_i         = self.xsize_i
            self.beam_i          = self.setbeam(mode='image')
            self.beam_s          = None
        elif mode == 'source':
            self.bmaj_s          = bmaj * 3600
            self.bmin_s          = bmin * 3600
            self.bpa_s           = bpa * np.pi / 180
            self.dx_s, self.dy_s = dx, dy
            self.xsize_s         = toodd(self.bmaj_s / self.dx_s * 2)  # 2 * FWHM
            self.ysize_s         = self.xsize_s
            self.beam_i          = None
            self.beam_s          = self.setbeam(mode='source')

    def setbeam(self, mode):
        conv = 2 * np.sqrt(2 * np.log(2))
        if mode == 'image':
            xmin_i, ymin_i     = -(self.xsize_i - 1) / 2, -(self.ysize_i - 1) / 2
            xmax_i, ymax_i     = (self.xsize_i - 1) / 2, (self.ysize_i - 1) / 2
            x_i, y_i           = np.linspace(xmin_i*self.dx_i, xmax_i*self.dx_i, self.xsize_i), \
                                 np.linspace(ymin_i*self.dy_i, ymax_i*self.dy_i, self.ysize_i)
            self.X_i, self.Y_i = np.meshgrid(x_i, y_i)
            Z_i                = gauss(np.cos(-self.bpa_i) * self.X_i - np.sin(-self.bpa_i) * self.Y_i, 0, self.bmin_i / conv) * \
                                 gauss(np.sin(-self.bpa_i) * self.X_i + np.cos(-self.bpa_i) * self.Y_i, 0, self.bmaj_i / conv) * \
                                 self.dx_i * self.dy_i

            return Z_i
        elif mode == 'source':
            xmin_s, ymin_s     = -(self.xsize_s - 1) / 2, -(self.ysize_s - 1) / 2
            xmax_s, ymax_s     = (self.xsize_s - 1) / 2, (self.ysize_s - 1) / 2
            x_s, y_s           = np.linspace(xmin_s*self.dx_s, xmax_s*self.dx_s, self.xsize_s), \
                                 np.linspace(ymin_s*self.dy_s, ymax_s*self.dy_s, self.ysize_s)
            self.X_s, self.Y_s = np.meshgrid(x_s, y_s)
            Z_s                = gauss(np.cos(-self.bpa_s) * self.X_s - np.sin(-self.bpa_s) * self.Y_s, 0, self.bmin_s / conv) * \
                                 gauss(np.sin(-self.bpa_s) * self.X_s + np.cos(-self.bpa_s) * self.Y_s, 0, self.bmaj_s / conv) * \
                                 self.dx_s * self.dy_s

            return Z_s

    def calcbeam_i(self, dx_i, dy_i, kappa, gamma, phi):
        conv  = 2 * np.sqrt(2 * np.log(2))
        Kappa = 1 - (1 - kappa) / ((1 - kappa)**2 - gamma**2)
        Gamma = -gamma / ((1 - kappa)**2 - gamma**2)
        Phi   = phi

        # a, b <-> sigma (not FWHM)
        a, b = self.bmin_s / conv, self.bmaj_s / conv

        if a != b:
            v1   = a * (1 - Kappa - Gamma) * np.cos(self.bpa_s - Phi)
            v2   = b * (1 - Kappa - Gamma) * np.sin(self.bpa_s - Phi)
            v3   = a * (1 - Kappa + Gamma) * np.sin(self.bpa_s - Phi)
            v4   = b * (1 - Kappa + Gamma) * np.cos(self.bpa_s - Phi)

            phi0  = 1. / 2 * np.arctan(2 * (v1*v2 - v3*v4) / (v1**2 - v2**2 + v3**2 - v4**2))
            Theta = np.arctan((v3 * np.cos(phi0) - v4 * np.sin(phi0)) / (v1 * np.cos(phi0) + v2 * np.sin(phi0)))        
            a2    = np.abs((v1 * np.cos(phi0) + v2 * np.sin(phi0)) / np.cos(Theta))
            b2    = np.abs((v3 * np.sin(phi0) + v4 * np.cos(phi0)) / np.cos(Theta))
            theta = Theta + phi
        else:
            a2 = np.abs(a * (1 - Kappa - Gamma))
            b2 = np.abs(a * (1 - Kappa + Gamma))
            theta = Phi

        self.a2, self.b2, self.theta = a2, b2, theta

        self.dx_i, self.dy_i = dx_i, dy_i
        if a2 > b2:
            self.bmaj_i  = a2 * conv
            self.bmin_i  = b2 * conv
            self.bpa_i   = theta - np.pi / 2
            self.xsize_i = toodd(a2 * conv / self.dx_i * 2)  # 2 * FWHM
        else:
            self.bmaj_i  = b2 * conv
            self.bmin_i  = a2 * conv
            self.bpa_i   = theta
            self.xsize_i = toodd(b2 * conv / self.dx_i * 2)  # 2 * FWHM
        self.ysize_i = self.xsize_i

        xmin_i, ymin_i     = -(self.xsize_i - 1) / 2, -(self.ysize_i - 1) / 2
        xmax_i, ymax_i     = (self.xsize_i - 1) / 2, (self.ysize_i - 1) / 2
        x_i, y_i           = np.linspace(xmin_i*self.dx_i, xmax_i*self.dx_i, self.xsize_i), \
                             np.linspace(ymin_i*self.dy_i, ymax_i*self.dy_i, self.ysize_i)
        self.X_i, self.Y_i = np.meshgrid(x_i, y_i)        
        Z_i                = gauss(np.cos(-theta) * self.X_i - np.sin(-theta) * self.Y_i, 0, a2) * \
                             gauss(np.sin(-theta) * self.X_i + np.cos(-theta) * self.Y_i, 0, b2) * \
                             self.dx_i * self.dy_i
        self.beam_i = Z_i

        return Z_i

    def calcbeam_s(self, dx_s, dy_s, kappa, gamma, phi):
        conv = 2 * np.sqrt(2 * np.log(2))

        # a, b <-> sigma (not FWHM)
        a, b = self.bmin_i / conv, self.bmaj_i / conv
        v1   = a * (1 - kappa - gamma) * np.cos(self.bpa_i - phi)
        v2   = b * (1 - kappa - gamma) * np.sin(self.bpa_i - phi)
        v3   = a * (1 - kappa + gamma) * np.sin(self.bpa_i - phi)
        v4   = b * (1 - kappa + gamma) * np.cos(self.bpa_i - phi)

        phi0  = 1. / 2 * np.arctan(2 * (v1*v2 - v3*v4) / (v1**2 - v2**2 + v3**2 - v4**2))
        Theta = np.arctan((v3 * np.cos(phi0) - v4 * np.sin(phi0)) / (v1 * np.cos(phi0) + v2 * np.sin(phi0)))
        a2    = np.abs((v1 * np.cos(phi0) + v2 * np.sin(phi0)) / np.cos(Theta))
        b2    = np.abs((v3 * np.sin(phi0) + v4 * np.cos(phi0)) / np.cos(Theta))
        theta = Theta + phi

        self.dx_s, self.dy_s = dx_s, dy_s
        if a2 > b2:
            self.bmaj_s  = a2 * conv
            self.bmin_s  = b2 * conv
            self.bpa_s   = theta - np.pi / 2
            self.xsize_s = toodd(a2 * conv / self.dx_s * 2)  # 2 * FWHM
        else:
            self.bmaj_s  = b2 * conv
            self.bmin_s  = a2 * conv
            self.bpa_s   = theta
            self.xsize_s = toodd(b2 * conv / self.dx_s * 2)  # 2 * FWHM
        self.ysize_s = self.xsize_s

        xmin_s, ymin_s     = -(self.xsize_s - 1) / 2, -(self.ysize_s - 1) / 2
        xmax_s, ymax_s     = (self.xsize_s - 1) / 2, (self.ysize_s - 1) / 2
        x_s, y_s           = np.linspace(xmin_s*self.dx_s, xmax_s*self.dx_s, self.xsize_s), \
                             np.linspace(ymin_s*self.dy_s, ymax_s*self.dy_s, self.ysize_s)
        self.X_s, self.Y_s = np.meshgrid(x_s, y_s)        
        Z_s                = gauss(np.cos(-theta) * self.X_s - np.sin(-theta) * self.Y_s, 0, a2) * \
                             gauss(np.sin(-theta) * self.X_s + np.cos(-theta) * self.Y_s, 0, b2) * \
                             self.dx_s * self.dy_s
        self.beam_s = Z_s

        return Z_s

    def convolve(self, fitscls, mode):
        if mode == 'image':
            fitscls.data = _convolve(fitscls.data, self.beam_i)
        elif mode == 'source':
            fitscls.data = _convolve(fitscls.data, self.beam_s)

    # def plot2D(self, mode):
    #     fig = plt.figure()
    #     ax  = fig.add_subplot(111, aspect='equal')
    #     if mode == 'image':
    #         ax.contour(self.X_i, self.Y_i, self.beam_i)
    #     elif mode == 'source':
    #         ax.contour(self.X_s, self.Y_s, self.beam_s)
    #     fig.show()

    # def plot3D(self, mode):
    #     fig = plt.figure()
    #     ax  = Axes3D(fig)
    #     if mode == 'image':
    #         ax.plot_wireframe(self.X_i, self.Y_i, self.beam_i)
    #     elif mode == 'source':
    #         ax.plot_wireframe(self.X_s, self.Y_s, self.beam_s)
    #     fig.show()
