import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 5):
    raise Exception("interactive_python makes use of asyncio, async, and"
                    "await, and therefore requires Python >= 3.5.x")

setup(
    name='interactive_python',
    version='0.1.0',
    description='Reference API implementation for Mixer Interactive 2',
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
    author_email='connor@xbox.com',
    url='https://github.com/mixer/interactive-python',
    license='MIT',
    packages=find_packages(exclude=['tests']),
    install_requires=['websockets>=3.3', 'varint>=1.0.2', 'pyee>=3.0.3',
                      'aiohttp>=2.0.7'],
    include_package_data=True,
)
