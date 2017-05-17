import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 5):
    raise Exception("beam-interactive-python2 makes use of asyncio, async," +
                    "and await, and therefore requires Python >= 3.5.x")

setup(
    name='beam_interactive2',
    version='0.1.0',
    description='Reference game client implementation for Beam Interactive 2',
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'License :: OSI Approved :: MIT License',
        'Topic :: Games/Entertainment',
        'Topic :: Software Development',
        'Topic :: Software Development :: Libraries'
    ],
    author='Connor Peet',
    author_email='connor@peet.io',
    url='https://github.com/WatchBeam/beam-interactive-python2',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    install_requires=['websockets>=3.3', 'varint>=1.0.2', 'pyee>=3.0.3',
                      'aiohttp>=2.0.7'],
    include_package_data=True,
)
