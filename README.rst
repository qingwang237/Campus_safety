==========================================================
On Campus Crime Data API deployed on AWS Lambda with Zappa
==========================================================

Overview
========

To deploy it with zappa, AWS config and credentials files should be put under
~/.aws/

The context of these two files should be like this:

~/.aws/config::

   [default]

   region=us-west-2

   output=json

The credentials file should be like:

~/.aws/credentials::

   [default]

   aws_access_key_id = XXXXXXXXXXXXXXXX

   aws_secret_access_key = XXXXXXXXXXXXXXXXXX


Project Files
=============
**my_app.py**    The main Flask app.

**zappa_settings.json**  Zappa configuration file.


Setup development envrionment and Deployment
============================================
To set up the python development, in the folder of the project, run::

    virtualenv --no-site-packages env

then activate the new environment by::

    source env/bin/activate

after this, install all the dependencies by run::

    pip install -r requirements.txt

then it's done.

To run the app locally, you can do like this::

    python my_app.py

To deploy the app, after setup the AWS credentials and virtual environment, run::

    zappa update dev
