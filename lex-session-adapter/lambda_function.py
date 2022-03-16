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
import os
import json
import logging
import boto3
import base64
import gzip


logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize boto3 client at global scope for connection reuse
lexClient = boto3.client('lexv2-runtime')


def lambda_handler(event, context):

    # Step 1: Retrieve/validate input values
    try:
        logger.info('lambda_handler: event = ' + json.dumps(event))
        urlpath = event.get("path", None)
        
        if urlpath == "/session":
            body = event.get("body")
            if body:
                body=json.loads(body)
            else:
                body={}
        else:
            status = "error"
            status_message = "Invalid url configuration"
            return close(status, status_message, {})
    
    except KeyError as e:
        logger.error('Exception retrieving values from event: missing key')
        status = "error"
        status_message = "Configuration error"
        return close(status, status_message, {})

    locale = 'en_US'
    sessionId=body.get("participantId", None)
    attributes=body.get("attributes", {})
    action=body.get("action", None)
    
    if sessionId is None or action is None:
        logger.error('lambda_handler: configuration error: no participantId or action type provided.')
        errorMessage = "no participantId or action type provided"
        return close("error", errorMessage, {})


    # Step 2: Retrieve Lex bot configuration information
    lexBotId = os.environ.get('LEX_BOT_ID', None)
    lexBotAliasId = os.environ.get('LEX_BOT_ALIAS_ID', None)
    
    if lexBotId is None or lexBotAliasId is None:
        logger.error('lambda_handler: configuration error: unable to retrieve Lex bot name and alias environment variables.')
        errorMessage = "Sorry, the API gateway is not configured with an Amazon Lex bot."
        return close("error", errorMessage, {})
 
 
    # Step 3: Get existing Lex session attributes, if available
    try:
        getresp = lexClient.get_session(
            botId=lexBotId,
            botAliasId=lexBotAliasId,
            localeId=locale,
            sessionId=sessionId
        )
        
        # get session attributes and remove any null values
        session_attributes = {k: v for k, v in getresp["sessionState"]["sessionAttributes"].items() if v is not None}
        #gather slots and session state data
        slots = getresp["sessionState"]["intent"]["slots"]
        session_state = getresp["sessionState"]
        
    except Exception as e:
        # no session attributes available
        session_attributes = {}
        status = "error"
        logger.error('lex get session error: ' + str(e))
        status_message = "lex get session error: " + str(e)
        return close(status, status_message, session_attributes)


    # Step 4: determine action
    if action == "get":
        status= "success"
        message = 'lex get session'
        
    elif action == "put":
        #Update null slots to empty dict. put_session does not like null.
        for slot in slots:
            if not slots[slot]:
                session_state["intent"]["slots"][slot] = {}

        #Add/update any provided attributes
        for attr in attributes:
            session_state["sessionAttributes"][attr] = attributes[attr]
        
        try:
            putresp = lexClient.put_session(
                botId=lexBotId,
                botAliasId=lexBotAliasId,
                localeId=locale,
                sessionId=sessionId,
                sessionState=session_state,
                responseContentType='text/plain; charset=utf-8'
            )
        
            # response string is base64 encoded gzip data
            gzipBytes = base64.b64decode(putresp["sessionState"])
            ss_data_bytes = gzip.decompress(gzipBytes)
            
            #set session_state to current put session response
            session_state = json.loads(ss_data_bytes.decode())
            # get session attributes and remove any null values
            session_attributes = {k: v for k, v in session_state["sessionAttributes"].items() if v is not None}
            status = "success"
            message="lex put session"
        
        except Exception as e:
            # no session attributes available
            session_attributes = {}
            status = "error"
            logger.error('lex put session error: ' + str(e))
            status_message = "lex put session error: " + str(e)
            return close(status, status_message, session_attributes)

    else:
        status= "error"
        message = 'unknow action type: ' + str(action)
        session_attributes = {}
    
    logger.info('Action %s, API Call status: %s, Message: %s', action, status, message)
    logger.info('Lex sessionState: ' + json.dumps(session_state))   
    return close(status, message, session_attributes)
    

def close(status, message_text, attributes):
    return_value = {
            "statusCode": 200,
            'headers': {
            'Access-Control-Allow-Headers': 'Content-Type,Authorization,X-Amz-Date,X-Api-Key,X-Amz-Security-Token',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'OPTIONS,POST'
            },
            "body": json.dumps({
                "status": status,
                "message": message_text,
                "attributes": attributes
            })
        }    

    return return_value