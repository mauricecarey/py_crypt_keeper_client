#   Copyright 2017 Maurice Carey
#
#    Licensed under the Apache License, Version 2.0 (the "License");
#    you may not use this file except in compliance with the License.
#    You may obtain a copy of the License at
#
#        http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS,
#    WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#    See the License for the specific language governing permissions and
#    limitations under the License.
#

from setuptools import setup

setup(
    name='py_crypt_keeper_client',
    version='0.1',
    description='A Python client for the Crypt-Keeper service.',
    url='http://github.com/mauricecarey/py_crypt_keeper_client',
    author='Maurice Carey',
    author_email='maurice@mauricecarey.com',
    license='Apache License, Version 2.0',
    packages=['py_crypt_keeper_client'],
    install_requires=[
        'pycrypto==2.6.1',
        'requests==2.11.1',
        'requests-toolbelt==0.7.0',
    ],
    zip_safe=False,
    entry_points={
        'console_scripts': ['ckc=py_crypt_keeper_client.command:main'],
    },
)
