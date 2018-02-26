from distutils.core import setup
import py2exe

setup(console=['main.py'], requires=['pyqt5-tools', 'PyQt5', 'reportlab', 'xlrd', 'pyvisa', 'numpy', 'pyserial',
                                     'matplotlib', 'drawnow'])