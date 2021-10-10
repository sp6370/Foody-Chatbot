import json
import boto3

def lambda_handler(event, context):
    botClient = boto3.client('lex-runtime')
    userID = "USER101"
    botName = "DiningBot"
    botAlias = "test_Bot_a"
    rawUserInput = event.get('messages')
    userInput = rawUserInput[0].get("unstructured").get('text')
    
    botResponse = botClient.post_text(
        botName = botName,
        botAlias = botAlias,
        userId = userID,
        inputText = userInput
        )
        
    return {
        'statusCode': 200,
        'headers': { 
            "Access-Control-Allow-Origin": "*" 
        },
        'messages': [{
            'type' : 'unstructured',
            'unstructured' :{
                'text' : botResponse["message"]
                }
            }]
        }
