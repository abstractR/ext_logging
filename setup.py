#!python
from ext_logging import VERSION
from setuptools import setup, find_packages

entry_points = {
    'console_scripts': [
        'ngrep = ext_logging.scripts.ngrep.py',
    ]
}

setup(
    name='ext_logging',
    version=VERSION,
    description='Advanced Logging for Ops writing in Python',
    author='Sergii Pylypenko',
    author_email='serj.pilipenko@gmail.com',
    packages=find_packages(),
    include_package_data=True,
    install_requires=list(open('requirements.txt').readlines()),
    scripts=['ext_logging/scripts/ngrep.py'],
)
