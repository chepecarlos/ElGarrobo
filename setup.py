from setuptools import find_packages
from setuptools import setup

with open("VERSION", 'r') as f:
    version = f.read().strip()

with open("README.md", 'r') as f:
    long_description = f.read()

setup(
    name='elgatoalsw',
    version=version,
    description='Heramienta Macros de ALSW',
    author='ChepeCarlos',
    author_email='chepecarlos@alsw.net',
    url='https://github.com/chepecarlos/ElGatoALSW',
    install_requires=[],
    packages=find_packages(where='src', exclude=('tests*', 'testing*')),
    package_dir={"": "src"},
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires='>=3.8',
    entry_points={
        'console_scripts': [
            'elgatoalsw-cli = elgatoalsw.elgatoalsw:main'
        ]
    }
)
