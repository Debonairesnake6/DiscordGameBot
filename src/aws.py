"""
Handles the interactions with the AWS bucket
"""

import os
import boto3
from botocore.exceptions import NoCredentialsError


class AWSHandler:
    """
    Handle the functionality when communicating with AWS
    """

    def __init__(self):
        self.auth = boto3.client('s3', aws_access_key_id=os.environ['AWSAccessKeyId'], aws_secret_access_key=os.environ['AWSSecretKey'])

    def upload_image(self, user: str, filename: str):
        """
        Upload the current game image to AWS

        :param user: ID of the user whom the file is being uploaded in relation to.
        :param filename: Name of the file to load and save as on AWS. e.g. user_info.jpg
        """

        try:
            self.auth.upload_file(f'../extra_files/{user}_{filename}',
                                  'discordgamebotimages',
                                  f'{user}_{filename}',
                                  ExtraArgs={'GrantRead': 'uri=http://acs.amazonaws.com/groups/global/AllUsers'})
        except FileNotFoundError:
            pass
        except NoCredentialsError:
            pass
