from setuptools import setup

setup(
    name='py_crypt_keeper_client',
    version='0.1',
    description='A Python client for the Crypt-Keeper service.',
    url='http://github.com/mauricecarey/py_crypt_keeper_client',
    author='Maurice Carey',
    author_email='maurice@mauricecarey.com',
    license='Apache 2.0',
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
