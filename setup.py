from setuptools import setup, find_packages


setup(
    name='bratlib',
    packages=find_packages(),
    version='0.0.0',
    description='Data facilitation for BRAT annotations',
    author='Steele Farnsworth',
    install_requires=[
        'cached-property',
        'pandas'
    ]
)