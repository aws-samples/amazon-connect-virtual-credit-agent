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
import boto3
import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize boto3 client at global scope
connectClient = boto3.client('connect')


def start_chat_contact(body):
    contact_flow_id = body.get("ContactFlowId", None)
    instance_id = body.get("InstanceId", None)
    logger.info('InstanceId: %s, FlowId: %s', instance_id, contact_flow_id)

    try:
        response = connectClient.start_chat_contact(
            InstanceId=instance_id,
            ContactFlowId=contact_flow_id,
            Attributes={
                "customerName": body["ParticipantDetails"]["DisplayName"]
            },
            ParticipantDetails={
                "DisplayName": body["ParticipantDetails"]["DisplayName"]
            }
        )
        logger.info('start chat contact response: ' + json.dumps(response))
        return successful_response(response)
    
    except Exception as e:
        logger.error('start chat contact error: ' + str(e))
        return error_response(str(e))


def successful_response(result):
    response = {
        "statusCode": 200,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            'Content-Type': 'application/json',
            'Access-Control-Allow-Credentials': True,
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        },
        "body": json.dumps({
            "data": {"startChatResult": result}
        })
    }
    return response


def error_response(err):
    response = {
        "statusCode": 500,
        "headers": {
            "Access-Control-Allow-Origin": "*",
            'Content-Type': 'application/json',
            'Access-Control-Allow-Credentials': True,
            'Access-Control-Allow-Headers': 'Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token'
        },
        "body": json.dumps({
            "data": {
                "Error": err
            }
        })
    }
    return response


def lambda_handler(event, context):
    logger.info('lambda_handler: chat request event = ' + json.dumps(event))
    body = json.loads(event.get("body"))
    return start_chat_contact(body)
