from azure.storage.blob import BlobServiceClient
from django.conf import settings
import os

blob_service = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
container_client = blob_service.get_container_client(settings.AZURE_CONTAINER_NAME)

def upload_to_azure(local_file_path, blob_name):
    """Uploads a file to Azure Blob Storage and returns its URL"""

    with open(local_file_path, "rb") as data:
        container_client.upload_blob(blob_name, data, overwrite=True)

    return f"{settings.MEDIA_URL}{blob_name}"
