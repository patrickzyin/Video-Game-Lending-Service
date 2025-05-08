from storages.backends.s3boto3 import S3Boto3Storage

class CatalogMediaStorage(S3Boto3Storage):
    location = 'items'  # Upload game images to the 'items/' folder
    file_overwrite = False
