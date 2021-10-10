import json
from postmarker.core import PostmarkClient
import random
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
import boto3
import random
from botocore.exceptions import ClientError

def getCuisineRest(cuisine):
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
    q = cuisine
    query = {
        'size': 20,
        'query': {
            'multi_match': {
            'query': q,
            'fields': ['cuisine']
            }
            }
        }
    response = search.search(
        body = query,
        index = 'rdata'
        )
    rlist = response['hits']['hits']
    num = random.randint(0,len(rlist)-1)
    tmpDict = rlist[num]
    rid = tmpDict['_source']['restaurentID']
    return rid

#Config
awsRegion = 'us-east-1'
accessID='AKIATASZEMXJPWS65IPL'
secretKey = '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'
postmarkerKey = 'b55ae585-0a84-44b5-a1e7-2f0f3f0317b4'
dbObject = boto3.resource('dynamodb',region_name=awsRegion, aws_access_key_id=accessID, aws_secret_access_key=secretKey)
dbtable = dbObject.Table('restaurent_data')

def getData(rID, dbtable):
    try:
        response = dbtable.get_item(Key={'id': rID})
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        return response['Item']

def sendEmail(email, cuisine, dataDict):
    postmark = PostmarkClient(server_token=postmarkerKey)
    address = ''
    for tmp in dataDict['address']:
        address = address + ' ' + tmp

    msg = 'You can visit restaurent ' + dataDict['restaurent_name'] + ' at ' + tmp + ' ' + 'it serves great ' + cuisine + ' food.'
    postmark.emails.send(
        From='sp6370@nyu.edu',
        To=email,
        Subject='Restaurent Recommendation',
        HtmlBody= msg)

def checkSqsStatus():
    sqsObject = boto3.client('sqs')
    queues = sqsObject.list_queues(QueueNamePrefix='botQueue')
    queueURL = queues['QueueUrls'][0]

    while True:
        queueResponse = sqsObject.receive_message(
            QueueUrl=queueURL,
            AttributeNames=[
                'All'
            ],
            MaxNumberOfMessages=10,
            MessageAttributeNames=[
                'All'
            ],
            VisibilityTimeout=30,
            WaitTimeSeconds=0
        )

        if 'Messages' in queueResponse:
            for message in queueResponse['Messages']:
                queueMessageData = json.loads(message['Body'])
                email = queueMessageData['email']
                cuisine = queueMessageData['cuisine']
                rid = getCuisineRest(cuisine)
                data = getData(rid, dbtable)
                sendEmail(email, cuisine, data)
                print(queueMessageData)
                sqsObject.delete_message(QueueUrl=queueURL, ReceiptHandle=message['ReceiptHandle'])
        else:
            print('Queue is now empty')
            break

def lambda_handler(event, context):
    checkSqsStatus()