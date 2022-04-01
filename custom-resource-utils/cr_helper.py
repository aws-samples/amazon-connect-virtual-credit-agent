import urllib.request
import json
import logging
import config_utils as utils

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def send_response(event, log_stream_name, response_status, response_data):
    msg = "See the details in CloudWatch Log Stream: " + str(log_stream_name)
    data = json.dumps({
        "Status": response_status,
        "Reason": msg,
        "PhysicalResourceId": log_stream_name,
        "StackId": event['StackId'],
        "RequestId": event['RequestId'],
        "LogicalResourceId": event['LogicalResourceId'],
        "Data": response_data
    })

    length_of_response = len(data)
    data = bytes(data, 'utf-8')
    url = event['ResponseURL']
    # Build request
    req = urllib.request.Request(url=url, data=data, method='PUT')
    req.add_header("Content-Type", "")
    req.add_header("Content-Length", str(length_of_response))
    try:
        response = urllib.request.urlopen(req)
    except Exception as e:
        logger.info("Error executing PUT to S3 URL")
        print(e)
    else:
        logger.info("Successfully executed PUT to S3 URL")


def process_event(event, context):
    request_type = event['RequestType']
    custom_action = event['ResourceProperties'].get("customAction", None)
    resource_properties = event['ResourceProperties']
    
    logger.info("Request Type: %s", request_type)
    logger.info("Custom Action: %s", custom_action)

    # default status
    response_status = 'FAILED'
    response_data = None    
    
    if not custom_action:
        logger.info("Error: No customAction defined in CFN resource properties.")
        send_response(event, context.log_stream_name, response_status, response_data)
        return
 
    # Take actions based on request type and custom action
    if request_type == "Delete":
        # Disassociate bot on delete
        if custom_action == "configureConnectBot":
            logger.info("Disassociate bot from Connect Instance")
            response_status = utils.disassociate_bot(resource_properties)
        else:
            logger.info("No action taken")
            response_status = 'SUCCESS'
        send_response(event, context.log_stream_name, response_status, response_data)

    elif request_type == "Create" or request_type == "Update":
        # Associate bot on create only
        if custom_action == "configureConnectBot" and request_type == "Create":
            logger.info("Associate bot to Connect Instance")
            response_status = utils.associate_bot(resource_properties)

        # Copy website files
        if custom_action == "configureWebsite":
            logger.info("Copy website files")
            response_status = utils.copy_website_files(resource_properties)
        
        # Configure index file
        if custom_action == "configureIndexFile":
            logger.info("Configure index file")
            response_status = utils.config_index_file(resource_properties)
                
        send_response(event, context.log_stream_name, response_status, response_data)

    else:
        logger.info("Error: Unknown request type")


def lambda_handler(event, context):
    logger.info('lambda_handler: CFN event = ' + json.dumps(event))
    return process_event(event, context)
