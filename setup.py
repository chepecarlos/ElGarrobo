from setuptools import find_packages
from setuptools import setup

with open(file="README.md", mode="r") as readme_handle:
    long_description = readme_handle.read()

setup(
    name='elgatoalsw',
    version='0.0.5',
    description='Heramienta Macros de ALSW',
    long_description=long_description,
    author='ChepeCarlos',
    author_email='chepecarlos@alswblog.org',
    url='https://github.com/chepecarlos/ElGatoALSW',
    install_requires=[],
    packages=find_packages(where='src', exclude=('tests*', 'testing*')),
    package_dir={"": "src"},
    entry_points={
        'console_scripts': [
            'elgatoalsw-cli = elgatoalsw.main:main'
        ]
    },
)
