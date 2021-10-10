import requests
import json
import boto3
from datetime import datetime
import pickle

#globalConfig
cuisineTypes = ['chinese' ,' italian', 'mexican', 'french']
location = ['brooklyn', 'manhattan', 'bronx', 'queens', 'staten island']
businessType = 'restaurant'
radius ='40000'

#AWS Config
awsRegion = 'us-east-1'
accessID='AKIATASZEMXJPWS65IPL'
secretKey = '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'
dbObject = boto3.resource('dynamodb',region_name=awsRegion, aws_access_key_id=accessID, aws_secret_access_key=secretKey)
dbtable = dbObject.Table('restaurent_data')


#yelpConfig
yelpEndpoint='https://api.yelp.com/v3/businesses/search'
clientID='jTihVSDKH_pqc0dl3WmLcQ'
yelpKey='g1TMYvPLQg49GruLJmWvH4QllxwDu_aPv2DsEWfRt4ivSio3_ZgbcuIuGyAGL0yBf3FYhrec42pW_gYrU13-qwgRkECgeRvjXqiUnEW63k66eRlYdv_kYn-fkbNgYXYx'
yelpConfig={'Authorization':'Bearer ' + yelpKey}

globalDict = {}
opensearchDict = {}

def updateDict(responseObject, cuisineType):
    print(responseObject)
    try:
        restaurentList = responseObject['businesses']
        if(len(restaurentList)>0):
                for i in range(len(restaurentList)):
                    tmpKey = restaurentList[i]['id']
                    if tmpKey in globalDict.keys():
                        continue
                    else:
                        tmpValue = {
                                'id': restaurentList[i]['id'],
                                'restaurent_name': restaurentList[i]['name'],
                                'address': restaurentList[i]['location']['display_address'],
                                'zip_code' : restaurentList[i]['location']['zip_code'],
                                'timestamp': datetime.now().strftime("%m/%d/%Y, %H:%M:%S")
                            }
                        globalDict[tmpKey] = tmpValue
                        opensearchTmpValue = {'id': restaurentList[i]['id'],'cuisine':cuisineType}
                        opensearchDict[tmpKey] = opensearchTmpValue
    except:
        print('')

def yelpDataCollecter():
    for cuisine in cuisineTypes:
        for loc in location:
            offsetValue = 1
            for i in range(18):
                urlParameter = {'categories':cuisine,'location':loc, 'limit':50, 'offset':offsetValue,'radius': radius}
                apiResponse = requests.get(yelpEndpoint, headers = yelpConfig, params = urlParameter)
                jsonResponse = json.loads(apiResponse.content.decode("utf-8"))
                updateDict(jsonResponse,cuisine)
                offsetValue = offsetValue + 50

def dbInsert(restaurentDict):
    with dbtable.batch_writer() as writer:
        for tmpKey in restaurentDict:
            writer.put_item(
                Item=restaurentDict[tmpKey]
            )

def saveData(gDict, osDict):
    f = open("gdict.pkl","wb")
    pickle.dump(gDict,f)
    f.close()

    q = open("odict.pkl","wb")
    pickle.dump(osDict,q)
    q.close()

yelpDataCollecter()
print("Items in global dictionary:", len(globalDict))
print("Items in global dictionary:", len(opensearchDict))

saveData(globalDict, opensearchDict)
userInput = int(input("Do you want to update DynamoDb and Open Search?"))

if(userInput == 1):
    dbInsert(globalDict)
else:
    print("Ending program")
