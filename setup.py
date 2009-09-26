# setup.py
# Python packaging for fpdb

from distutils.core import setup

setup(name = 'fpdb',
    description = 'Free Poker Database',
    version = '0.10.999',
    author = 'FPDB team',
    author_email = 'fpdb-main@lists.sourceforge.net',
    packages = ['fpdb'],
    package_dir = { 'fpdb' : 'pyfpdb' },
    data_files = [
        ('/usr/share/doc/python-fpdb',
            ['docs/readme.txt', 'docs/release-notes.txt',
            'docs/tabledesign.html', 'THANKS.txt'])]
)
