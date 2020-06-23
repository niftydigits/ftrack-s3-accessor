# ftrack-s3-accessor

An ftrack s3 accessor updated to work with ftrack-python-api and boto3. 

## Requirements: 
- boto3 - if used standalone 
- ftrack-action-handler (optional) - if used with the transfer components action found [here](https://bitbucket.org/!api/2.0/snippets/ftrack/B6dX/f9e89e8bf95065a6fc0541dd058863ff1ddaceb6/files/transfer_components_action.py)

## Installation

Install python using pyenv:
    
    pyenv install

Install dependencies using pipenv (and python pyenv from above):

    pipenv install --python $(pyenv which python)

Note: To be able to make use the transfer components action, and be compatible with ftrack-connect the pipenv uses python 2.7. It works using other versions of python - remove the Pipfile.lock and the transfer_component dependency from the Pipfile, update the python version in .python-version and the Pipfile and re-run the install command.

## Configuration

Configure a new location within ftrack with the name 'studio.remote'. This will be used as the location for s3.

Create a storage bucket in s3 and set the bucket name using the FTRACK_S3_ACCESSOR_BUCKET environment variable (default: ftrack). Ensure your bucket name is globally unique and meets aws s3 naming restrictions.

Set all other ftrack environment variables for your ftrack instance. You can do so using an .env file for all your env vars which will automatically be loaded by pipenv when running scripts.

Running the scripts from within your pipenv requires you to additionally set your sources root to the accessor directory within your .env file.

    PYTHONPATH=./accessor` 

Ensure you have an working aws configuration under your ~/.aws folder. You can check this by running:
    
    pipenv run python

and then running:
    
    import boto3

If this fails, your aws configuration isn't setup properly. Refer to the [boto3](https://github.com/boto/boto3) documentation on how to set it up. You should only need a ~/.aws/config and ~/.aws/credentials file.

## Usage

The main plugin can be found in the plugins folder. This folder may be registered using the FTRACK_EVENT_PLUGIN_PATH ftrack environment variable so that it is picked up when ftrack is started.

Examples of how to use the plugin can be found in the scripts folder. The simplest way to launch ftrack with the accessor correctly pre-configured is:

    pipenv run start

Which will launch the start_ftrack_with_s3.py script. 

It is possible to use the [transfer components](https://bitbucket.org/!api/2.0/snippets/ftrack/B6dX/f9e89e8bf95065a6fc0541dd058863ff1ddaceb6/files/transfer_components_action.py) action to move components between local and remote storage. Ensure it is on the FTRACK_EVENT_PLUGIN_PATH (or add it to the plugins folder) and it should become available under ftracks actions menu. You will need to ensure your local storage is also correctly configured within a script when running the accessor outside of ftrack-connect, as the connect location configured by the desktop client will not be available as an option.
