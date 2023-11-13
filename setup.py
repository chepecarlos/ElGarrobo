from setuptools import find_packages, setup

with open("VERSION", "r") as f:
    version = f.read().strip()

with open("README.md", "r") as f:
    long_description = f.read()

with open("requirements.txt", "r") as f:
    required = f.read().splitlines()

setup(
    name="elgatoalsw",
    version=version,
    description="Herramienta Macros de ALSW",
    author="ChepeCarlos",
    author_email="chepecarlos@alsw.net",
    url="https://github.com/chepecarlos/ElGatoALSW",
    project_urls={
        "Bug Tracker": "https://github.com/chepecarlos/ElGatoALSW/issues",
    },
    install_requires=required,
    packages=find_packages(where="src", exclude=("tests*", "testing*")),
    package_dir={"": "src"},
    # data_files={"data/*"},
    long_description=long_description,
    long_description_content_type="text/markdown",
    python_requires=">=3.8",
    entry_points={"console_scripts": ["elgatoalsw-cli = main.main:main"]},
    include_package_data = True,
    package_data = {
        '': ['*.md'],
    }
)
