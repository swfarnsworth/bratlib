from setuptools import setup, find_packages


setup(
    name='bratlib',
    packages=find_packages(),
    version='1.0.0',
    python_requires='>=3.6',
    description='Data facilitation for BRAT annotations',
    author='Steele Farnsworth',
    install_requires=[
        'cached-property',
        'numpy',
        'pandas'
    ],
    tests_require=['pytest'],
    extras_require={
        ':python_version == "3.6"': [
            'dataclasses'
        ],
    }
)
