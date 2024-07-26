# # import cv2
# # import csv
# # import numpy as np
# # from pathlib import Path
# # import time
# import logging
# # from gps_handler import GPSHandler
# import boto3



# class DataUpload:
#     def __init__(self):
#         self.logger = logging.getLogger(__name__)
#         self.s3 = boto3.resource('s3')


#     def upload_data(self, ):

import boto3
import os
from botocore.exceptions import NoCredentialsError
from botocore.exceptions import ClientError


class ImageUploader:
    def __init__(self):
        self.bucket_name = 'foxtow-488579170006'
        self.s3 = boto3.client('s3')
        self.folder_name = 'camera100'
    
    def create_folder(self):
        self.s3.put_object(Bucket=self.bucket_name, Key=(self.folder_name))
    
    def upload_file(self, folder_name, local_file_path):
        """
        Creates a file with specified content and uploads it to the given S3 bucket in a specified folder.
        
        :param folder_name: Name of the folder to be created in the bucket
        :param local_file_path: Name of the file to be created and uploaded
        :param content: Content to be written in the file
        :return: None
        """
        try:
            destination_file_name = local_file_path.split('/')[-1]
            destination_path = f'{self.folder_name}/{destination_file_name}'
            response = self.s3.upload_file(local_file_path, self.bucket_name, destination_file_name)
            print(response)

        except ClientError as e:
            print(repr(e))
            
            print(f"File '{file_name}' uploaded to folder '{folder_name}' in bucket '{self.bucket_name}' successfully.")
        except FileNotFoundError:
            print("The file was not found")
        except NoCredentialsError:
            print("Credentials not available")

    def list_local_files(self, directory):
        """
        Lists all files in the specified local directory.
        
        :param directory: Path to the local directory
        :return: List of file paths
        """
        try:
            # files = [os.path.join(directory, f) for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
            files = [os.path.join(directory, f) for f in os.listdir(directory)
                if os.path.isfile(os.path.join(directory, f)) and f.lower().endswith('overlay.jpg')]
            print(f"Files in directory '{directory}':")
            for file in files:
                self.upload_file(self.folder_name, file)
                print(file)
            return files
        except FileNotFoundError:
            print(f"The directory '{directory}' was not found.")
            return []

    
    def list_files_and_folders(self):
        """
        Lists all directories and files in the given S3 bucket.
        
        :return: None
        """
        try:
            # List objects in the bucket
            response = self.s3.list_objects_v2(Bucket=self.bucket_name)

            if 'Contents' in response:
                print(f"Contents of bucket '{self.bucket_name}':")
                for obj in response['Contents']:
                    print(obj['Key'])
            else:
                print(f"Bucket '{self.bucket_name}' is empty.")

        except NoCredentialsError:
            print("Credentials not available")


# Example usage
# uploader = ImageUploader()
# uploader.create_folder()
# print(uploader.list_local_files('/home/pi/AIcamera1/data/car'))
# uploader.list_files_and_folders()
