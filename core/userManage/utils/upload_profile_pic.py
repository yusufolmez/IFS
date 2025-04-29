import uuid
from azure.storage.blob import BlobServiceClient
from django.conf import settings

def upload_to_blob(file, container_name):
    if not file or not file.name:
        raise Exception("Yüklenen dosya geçersiz.")
    try:
        blob_service_client = BlobServiceClient.from_connection_string(settings.AZURE_CONNECTION_STRING)
        try:
            blob_service_client.create_container(container_name)
        except Exception:
            pass 
        container_client = blob_service_client.get_container_client(container_name)
        unique_filename = f"{uuid.uuid4()}_{file.name}"
        blob_client = container_client.get_blob_client(unique_filename)
        blob_client.upload_blob(file, overwrite=True)
        return blob_client.url
    except Exception as e:
        raise Exception(f"Blob yükleme hatası: {str(e)}")