from setuptools import setup, find_packages

setup(
    name='colorizer-terminator',
    packages=find_packages(),
    install_requires=[
        "numpy",
        "scikit-learn",
        "scikit-image",
        "hasel>=1.0.1"
    ],
    dependency_links = ["https://github.com/sumartoyo/hasel.git/tarball/master#egg=package-1.0.1"]
)
