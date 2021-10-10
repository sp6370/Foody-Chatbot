from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import pickle
import random


openSearchEndpoint = 'https://search-rest-data1-k2nyoxqzoo7bqyrosdibkttuh4.us-east-1.es.amazonaws.com/' 
region = 'us-east-1'
accessID='AKIATASZEMXJKMNA2U5V'
secretKey = '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'

service = 'es'
credentials = boto3.Session(region_name=region, aws_access_key_id=accessID, aws_secret_access_key=secretKey).get_credentials()
awsauth = AWS4Auth(accessID, secretKey, region, service, session_token=credentials.token)

search = OpenSearch(
    hosts = openSearchEndpoint,
    http_auth = awsauth,
    use_ssl = True,
    verify_certs = True,
    connection_class = RequestsHttpConnection
)

index_body = {
  'settings': {
    'index': {
      'number_of_shards': 4
    }
  }
}

response = search.indices.create('rdata', body=index_body)

print('\nCreating index:')
print(response)

pickle_file = open("odict.pkl", "rb")
oDict = pickle.load(pickle_file)

id = 1

for tmpKey in oDict.keys():
    print(tmpKey)
    print(oDict[tmpKey])
    try:        
        response = search.index(
            index = 'rdata',
            body = {
                'restaurentID': tmpKey,
                'cuisine': oDict[tmpKey]['cuisine']
            },
            refresh = True
            )
        id = id + 1

        print('\nAdding document:')
        print(response)
    except:
        print('')