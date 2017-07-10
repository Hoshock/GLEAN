# coding: utf-8
from setuptools import setup, find_packages

setup(
    name             = 'glean',
    version          = '0.91',
    description      = '',
    license          = 'MIT',
    author           = 'Tsuyoshi Ishida',
    author_email     = 'tishida@ioa.s.u-tokyo.ac.jp',
    url              = 'https://github.com/tsuyoshiishida/GLEAN',
    keywords         = 'astronomy lensing',
    packages         = find_packages(),
    install_requires = ['astropy>=1.3.3', 'matplotlib>=2.0.2', 'numpy>=1.13.0', 'readline>=6.2.4.1'],
    entry_points     = '''
    [console_scripts]
    glean = glean.main:main
    '''
)
