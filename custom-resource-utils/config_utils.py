import json
import boto3
from botocore.exceptions import BotoCoreError, ClientError
import logging
import io

logger = logging.getLogger()
logger.setLevel(logging.INFO)

#Source directory
source_dir = "deployment/"

#Files in scope. adjust as necessary
file_list = ["js/amazon-connect-chat-interface.js"]
index_file = "index.html"

#boto clients
connect_client = boto3.client("connect")
s3_client = boto3.client("s3")

#This function moves any static files to the website defined in the list above.
def copy_website_files(resource_properties):
    dest_bucket = resource_properties["destS3Bucket"]
    dest_prefix = resource_properties["destS3KeyPrefix"]
    
    #defaults
    response_status='FAILED'
    content_type=None

    for file in file_list:
        if file.endswith(".htm") or file.endswith(".html"):
            content_type = "text/html"
        elif file.endswith(".css"):
            content_type = "text/css"
        elif file.endswith(".js"):
            content_type = "application/javascript"    
        else:
            logger.info("Unknown file type: %s", file)
            response_status = 'FAILED'
            break
        
        #prepare for copy
        dest_key = dest_prefix + file
        copy_source = source_dir + file
        
        #Retrieve local file
        with open (copy_source, 'rb') as fileRead:
            filedat=fileRead.read()
        
        logger.info("Copying %s to bucket: %s key: %s", copy_source, dest_bucket, dest_key)
        try:
            resp = s3_client.put_object(
                Bucket=dest_bucket,
                Body=filedat,
                Key=dest_key,
                ContentType=content_type
            )
        except Exception as e:
            logger.error('S3 put file failed')
            logger.error(str(e))
            response_status = 'FAILED'
            break
        else:
            response_status = 'SUCCESS'        
    return response_status

#This function adds a Lex V2 bot to a Connect instance
def associate_bot(resource_properties):
    aliasarn = resource_properties["botAliasArn"]
    instance = resource_properties["instanceId"]    
    try:
        resp = connect_client.associate_bot(
            InstanceId=instance,
            LexV2Bot={
                "AliasArn": aliasarn
            }
        )
    except Exception as e:
        logger.error('Connect Instance associate bot call failed')
        logger.error(str(e))
        response_status = 'FAILED'
    else:
        response_status = 'SUCCESS'
        
    return response_status

#This function removes the bot from the instance.
def disassociate_bot(resource_properties):
    aliasarn = resource_properties["botAliasArn"]
    instance = resource_properties["instanceId"]
    try:
        resp = connect_client.disassociate_bot(
            InstanceId=instance,
            LexV2Bot={
                "AliasArn": aliasarn
            }
        )
    except Exception as e:
        logger.error('Connect Instance disassociate bot call failed')
        logger.error(str(e))
        response_status = 'FAILED'
    else:
        response_status = 'SUCCESS'
        
    return response_status

#This function customizes the index file for the webiste.
def config_index_file(resource_properties):
    dest_bucket = resource_properties["destS3Bucket"]
    dest_prefix = resource_properties["destS3KeyPrefix"]

    #Index file values
    api_id = resource_properties["apId"]
    region_name = resource_properties["Region"]
    instance_id = resource_properties["instanceId"]
    flow_id = resource_properties["flowId"]
    enable_status = resource_properties["enableAttach"]
    
    #default
    response_status='FAILED'
    
    #prepare for get
    source_file = source_dir + index_file

    #Get template file data
    with open (source_file, 'rt') as fileRead:
        file_data=fileRead.read()
    
    #Replace template data with actual values
    #Note: Just first occurrence
    file_data = file_data.replace('${region}', region_name, 1)
    file_data = file_data.replace('${apiId}', api_id, 1)
    file_data = file_data.replace('${instanceId}', instance_id, 1)
    file_data = file_data.replace('${contactFlowId}', flow_id, 1)
    file_data = file_data.replace('${enableAttachments}', enable_status, 1)
     
    #prepare data for put
    file_data_io = io.StringIO(file_data)
    dest_key_file = dest_prefix + index_file
    content_type = "text/html"
    
    #Put modified file
    try:
        resp = s3_client.put_object(
            Bucket=dest_bucket,
            Key=dest_key_file,
            Body=file_data_io.read(),
            ContentType=content_type
        )
    except Exception as e:
        logger.error('Put S3 index file failed')
        logger.error(str(e))
        response_status = 'FAILED'
        return response_status
    else:
        response_status = 'SUCCESS'
 
    return response_status