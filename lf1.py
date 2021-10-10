import math
import dateutil.parser
import datetime
import time
import os
import logging
import boto3
import json
import re

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

awsRegion = 'us-east-1'
accessID='AKIATASZEMXJPWS65IPL'
secretKey = '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'
sqs = boto3.resource('sqs',region_name=awsRegion, aws_access_key_id=accessID, aws_secret_access_key=secretKey)

def get_slots(intent_request):
    return intent_request['currentIntent']['slots']

def elicit_slot(session_attributes, intent_name, slots, slot_to_elicit, message):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'ElicitSlot',
            'intentName': intent_name,
            'slots': slots,
            'slotToElicit': slot_to_elicit,
            'message': message
        }
    }

def close(session_attributes, fulfillment_state, message):
    response = {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Close',
            'fulfillmentState': fulfillment_state,
            'message': message
        }
    }
    return response

def delegate(session_attributes, slots):
    return {
        'sessionAttributes': session_attributes,
        'dialogAction': {
            'type': 'Delegate',
            'slots': slots
        }
    }

def parse_int(n):
    try:
        return int(n)
    except ValueError:
        return float('nan')

def build_validation_result(is_valid, violated_slot, message_content):
    if message_content is None:
        return {
            "isValid": is_valid,
            "violatedSlot": violated_slot,
        }

    return {
        'isValid': is_valid,
        'violatedSlot': violated_slot,
        'message': {'contentType': 'PlainText', 'content': message_content}
    }

def isvalid_date(date):
    try:
        dateutil.parser.parse(date)
        return True
    except ValueError:
        return False


def validate_restaurant_request(cuisine_type, date, visit_time, pcount, email, loc):
    cuisineTypes = ['italian', 'mexican', 'french', 'chinese']
    if cuisine_type is not None and cuisine_type.lower() not in cuisineTypes:
        return build_validation_result(False,
                                       'cuisineType',
                                       'We do not have {}, would you like a different type of cuisine?  '
                                       'We have recommendations for italian, mexican, french, chinese.'.format(cuisine_type))

    if date is not None:
        if not isvalid_date(date):
            return build_validation_result(False, 'visitDate', 'I did not understand that, what date would you like to visit the restaurant? Please enter date in format YEAR-MM-DD.')
        elif datetime.datetime.strptime(date, '%Y-%m-%d').date() <= datetime.date.today():
            return build_validation_result(False, 'visitDate', 'You can visit restaurant from today or tomorrow onwards. When would you like to visit? Please enter date in format YEAR-MM-DD.')

    if visit_time is not None:
        if len(visit_time) != 5:
            return build_validation_result(False, 'visitTime', None)

        hour, minute = visit_time.split(':')
        hour = parse_int(hour)
        minute = parse_int(minute)
        if math.isnan(hour) or math.isnan(minute):
            return build_validation_result(False, 'visitTime', None)

        if hour < 10 or hour > 16:
            return build_validation_result(False, 'visitTime', 'Our business hours are from ten am. to five pm. Can you specify a time during this range?')

    if pcount is not None:
        pcount = int(pcount)
        if(pcount < 0 or  pcount > 20):
            return build_validation_result(False, 'peopleCount', 'We only have recommendations for people between 1 and 20. Please specify number of people between 1 and 20.')

    if email is not None:
        regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        if (re.fullmatch(regex, email)):
            print('')
        else:
            return build_validation_result(False, 'email', "Please enter valid email address.")
    
    if loc is not None:
        loc = loc.lower()
        if loc=='nyc' or loc=='new york' or loc=='new york city':
            print('')
        else:
            return build_validation_result(False, 'location', 'We currently have recommendations only for NYC. Please select NYC as the location.\nPlease enter location as NYC.')
    
    return build_validation_result(True, None, None)

def get_recommendation(intent_request):
    print(intent_request)
    source = intent_request['invocationSource']
    
    cuisine_type = get_slots(intent_request)["cuisineType"]
    date = get_slots(intent_request)["visitDate"]
    visit_time = get_slots(intent_request)["visitTime"]
    location = get_slots(intent_request)["location"]
    people = get_slots(intent_request)["peopleCount"]
    email = get_slots(intent_request)["email"]


    if source == 'DialogCodeHook':
        slots = get_slots(intent_request)
        validation_result = validate_restaurant_request(cuisine_type, date, visit_time, people, email, location)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(intent_request['sessionAttributes'],
                               intent_request['currentIntent']['name'],
                               slots,
                               validation_result['violatedSlot'],
                               validation_result['message'])

        output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
        return delegate(output_session_attributes, get_slots(intent_request))

    sqsQueue = sqs.get_queue_by_name(QueueName='botQueue')
    message = {"cuisine": cuisine_type, "email": email}
    sqsQueue.send_message(MessageBody=json.dumps(message))
    return close(intent_request['sessionAttributes'],
                 'Fulfilled',
                 {'contentType': 'PlainText',
                  'content': 'Stay tuned! We will shortly send our recommendation through email.'})

def dispatch(intent_request):
    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))
    intent_name = intent_request['currentIntent']['name']
    if intent_name == 'DiningSuggestionsIntent':
        return get_recommendation(intent_request)

    raise Exception('Intent with name ' + intent_name + ' not supported')

def lambda_handler(event, context):
    os.environ['TZ'] = 'America/New_York'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))
    return dispatch(event)