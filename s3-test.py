import logging
import boto3
from botocore.exceptions import ClientError
import pandas as pd
import io

s3_client = boto3.client('s3')
response = s3_client.list_buckets()
s3_resource = boto3.resource('s3')

BUCKET_NAME = 'ma-2020-06-flight-scraper'
FILE_NAME = 'flight_count.csv'
FILE_NAME_TEST = 'flight_count_test.csv'

# Output the bucket names
print('Existing buckets:')
for bucket in response['Buckets']:
    print(f'  {bucket["Name"]}')

# download file from bucket into local .csv
test = s3_resource.Object(BUCKET_NAME, FILE_NAME).download_file(FILE_NAME_TEST)

# read file from bucket into csv
obj = s3_client.get_object(Bucket= BUCKET_NAME , Key = FILE_NAME)
df = pd.read_csv(io.BytesIO(obj['Body'].read()), encoding='utf8')
print(df.head())

# write file to bucket
df.to_csv(f's3://{BUCKET_NAME}/{FILE_NAME_TEST}')