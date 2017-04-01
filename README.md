# Crypt-Keeper Client

## Install

To install using pip:

    virtualenv -p `which python3` some_env
    source some_env/bin/activate
    pip install py_crypt_keeper_client

## Development

### Getting (giting) the Code

Assuming you keep your source code in a directory names source off your home directory then do the following: 

    cd ~/source
    git clone http://github.com/mauricecarey/py_crypt_keeper_client

Note that you should likely fork the repo on GitHub before cloning to make it easier to send PRs if you intend to submit your changes back to the project. 

### Setting up a Virtual Environment
Assuming the directory structure as outlined above:

    cd ~/source/py_crypt_keeper_client
    virtualenv -p `which python3` env
    source env/bin/activate

### Installing Requirements for Development
Once you have your virtual environment setup and loaded:

    pip install -r requirements.txt

### Running Unit Tests
Nose is installed as part of the development requirements and we'll show examples of using nose here.

    nosetests py_crypt_keeper_client/tests/

or with coverage information:

    nosetests --with-coverage --cover-package=py_crypt_keeper_client py_crypt_keeper_client/tests/

Every attempt is made to keep coverage above a minimum of 85% with a goal of 95%, while it is understood that percentages are tricky when it comes to unit testing there are also far to many excuses for writing untested code. Keep this in mind if you are submitting PRs.

### Running Integration Tests
There is a simple integration test that communicates with the Crypt-Keeper service then executes a complete round trip file upload to S3 followed by grabbing the download info and downloading from S3. The randomly generated file is uploaded, downloaded, then compared for equality.

    python test.py
