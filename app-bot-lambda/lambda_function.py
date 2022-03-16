#
# Copyright 2021 Amazon.com, Inc. or its affiliates. All Rights Reserved.
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy of this
# software and associated documentation files (the "Software"), to deal in the Software
# without restriction, including without limitation the rights to use, copy, modify,
# merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED,
# INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A
# PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT
# HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE
# SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
#
import json
import logging
import lambda_helpers as helper
import utils

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Validation handler
def validate_handler(intent, active_contexts, session_attributes, messages, requestAttributes):
    intent_name = intent.get('name', None)
    slots = intent.get('slots', None)
    logger.info('Validation: %s %s', intent_name, json.dumps(slots))

    #Loan app intent
    if intent_name == 'LoanAppIntent':
        #check slots
        if not slots['loanType']:
            loan_types = [
                    {
                        "title": "auto"
                    },
                    {
                        "title": "home"
                    },
                    {
                        "title": "business"
                    }
            ]
            message = {
                'contentType': 'CustomPayload',
                'content': json.dumps(helper.listpicker_template(loan_types, "What type of loan do you want?"))
            }
            return helper.elicit_slot(intent, active_contexts, session_attributes, 'loanType', message, requestAttributes)
            
        if not slots['loanAmount']:    
            message = {
                'contentType': 'PlainText',
                'content': 'How much do you want to borrow?'
            }
            return helper.elicit_slot(intent, active_contexts, session_attributes, 'loanAmount', message, requestAttributes)
            
        if not slots['fileUpload']:
            message = {
                'contentType': 'PlainText',
                'content': 'Please upload an image of your wages document.'
            }
            return helper.elicit_slot(intent, active_contexts, session_attributes, 'fileUpload', message, requestAttributes)
            
    return helper.delegate(intent, active_contexts, session_attributes, messages, requestAttributes)
 

#Fulfillment handler
def fulfill_handler(intent, active_contexts, session_attributes, messages, requestAttributes):
    intent_name = intent.get('name', None)
    slots = intent.get('slots', None)
    logger.info('Fulfillment: %s, %s', intent_name, json.dumps(intent))
    logger.info('Fulfillment Session Attributes: %s', json.dumps(session_attributes, indent=4))

    #Intent based processing
    #Fallback
    if (intent_name == 'FallbackIntent'):
        #Basic 3 retry logic when in the fallback intent. Adjust/remove as necessary.
        intent['state'] = 'InProgress'
        if (not session_attributes.get('botTry', None)):
            session_attributes['botTry'] = '1'
        else:
            session_attributes['botTry'] = int(session_attributes['botTry']) + 1

        if (int(session_attributes['botTry']) < 3):
            if (int(session_attributes['botTry']) == 1):
                message = {
                    'contentType': 'PlainText',
                    'content': 'Sorry, but I don\'t understand. Can you please repeat your response?'
                }
            elif (int(session_attributes['botTry']) == 2):
                message = {
                    'contentType': 'PlainText',
                    'content': 'I still don\'t understand. Can you please repeat your response once more?'
                }
            return helper.elicit_intent(intent, active_contexts, session_attributes, message, requestAttributes)    
        else:
            intent['state'] = 'Fulfilled'
            message = {
                'contentType': 'PlainText',
                'content': 'I\'m sorry, but I cannot help at this time.'
            }
            del session_attributes['botTry']
            return helper.close(intent, active_contexts, session_attributes, message, requestAttributes)
    else:
        #LoanAppIntent
        #Confirm intent
        if (intent['confirmationState'] == 'None'):
            intent['state'] = 'InProgress'
            yes_no = [
                    {
                        "title": "yes"
                    },
                    {
                        "title": "no"
                    }
            ]
            message = {
                'contentType': 'CustomPayload',
                'content': json.dumps(helper.listpicker_template(yes_no, "Submit loan application?"))
            }
            return helper.confirm_intent(intent, active_contexts, session_attributes, message, requestAttributes)
            
        elif (intent['confirmationState'] == 'Denied'):
            #User said no to confirmation. Adjust this to meet your need.
            intent['state'] = 'Fulfilled'
            message = {
                "contentType": "PlainText",
                "content": "Ok. I've cancelled your loan request."
            }
            return helper.close(intent, active_contexts, session_attributes, message, requestAttributes)
            
        else:
            #User confirmed intent
            #loan approval evaluation
            loan_amount = int(slots['loanAmount']['value']['interpretedValue'])
            loan_type = str(slots['loanType']['value']['interpretedValue'])
            urlfile=session_attributes.get('urlfile', None)
            
            if not urlfile:
                intent['state'] = 'Failed'
                mycontenttype = "PlainText"
                mycontent="Sorry, but we are having technical difficulties. Please try again later." 
                message = {
                    "contentType": mycontenttype,
                    "content": mycontent
                }
                return helper.close(intent, active_contexts, session_attributes, message, requestAttributes)    
            
            #Retrieve image file
            urlbytes=helper.get_urlfile_bytes(urlfile)
            
            logger.info('Loan Evaluate: Type: %s, Amount: %s', loan_type, loan_amount)
            
            #Evaluate wage doc and check approval
            loan_response=utils.evaluate_loan(urlbytes, loan_amount)
            logger.info('Loan Response: %s', json.dumps(loan_response))
            
            #Respond to the client with results
            loan_message = loan_response['body']['message']
            intent['state'] = 'Fulfilled'
            mycontenttype = "PlainText"
            mycontent=loan_message 
            message = {
                "contentType": mycontenttype,
                "content": mycontent
            }
            return helper.close(intent, active_contexts, session_attributes, message, requestAttributes)    


#Main handler
def lambda_handler(event, context):
    logger.info('Lex Event: %s', json.dumps(event))
    
    #SessionState    
    session_attributes = event['sessionState'].get("sessionAttributes", {})
    intent = event['sessionState'].get("intent", {})
    active_contexts = event['sessionState'].get("activeContexts", [])
    
    #Messages
    messages = event.get("messages", [])
    
    #Request Attributes
    requestAttributes = event.get("requestAttributes", {})

    #Process based on source
    if ( event['invocationSource'] == 'DialogCodeHook'):
        return validate_handler(intent, active_contexts, session_attributes, messages, requestAttributes)    

    elif (event['invocationSource'] == 'FulfillmentCodeHook'):
        return fulfill_handler(intent, active_contexts, session_attributes, messages, requestAttributes) 

    else:
        logger.info('Event Error: %s', json.dumps(event))