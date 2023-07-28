from os import path
from setuptools import setup


here = path.abspath(path.dirname(__file__))
with open(path.join(here, 'README.md'), encoding='utf-8') as f:
    long_description = f.read()

setup(
    name='gauge-api-steps',
    version='0.9',
    description='Provides steps for a Gauge project, that runs tests against APIs',
    long_description=long_description,
    url='https://github.com/IBM/gauge-api-steps',
    author='Tobias Lehmann',
    author_email='derdualist1@gmail.com',
    license='MIT',
    packages=['gauge_api_steps'],
    install_requires=[
        'getgauge',
        'jsonpath-ng',
        'lxml>=4.9.2',
        'numexpr>=2.8.1',
    ],
    zip_safe=False
)
