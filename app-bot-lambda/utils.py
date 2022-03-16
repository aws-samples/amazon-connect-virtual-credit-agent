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
import boto3
from trp import Document


def evaluate_loan(imagebytes, busi_approval):
    # Amazon Textract client
    textract = boto3.client('textract')
    # Call Amazon Textract
    response = textract.analyze_document(
        Document={
            'Bytes': imagebytes
        },
        FeatureTypes=["FORMS"])

    #print(response)
    doc = Document(response)

    for page in doc.pages:
        #Get field by key
        key = "Social security wages"
        field = page.form.getFieldByKey(key)
        if(field):
            print("Key: {}, Value: {}".format(field.key, field.value))
    
        # Search fields by key
        fields = page.form.searchFieldsByKey(key)
        for field in fields:
            print("Key: {}, Value: {}".format(field.key, field.value))
            wages = field.value
            wagesstring = str(field.value)
            wagesstring = wagesstring.replace(",",'')
            wagesint = int(float(wagesstring))
            return makedecision(busi_approval,wagesint)

def makedecision (busi_approval, wagesint):
    if (wagesint * .5) > busi_approval:
        creditdecision = "Approved"
        Message="Congratulations! Your loan is approved. I'll now tranfer you to an agent for help with processing your loan."
        print(creditdecision)
    else:
        creditdecision = "Denied"
        Message="Your load has been denied. I'll transfer you to an agent for further assistance."
        print(creditdecision)

    return {
        "response": creditdecision,
        "body": {
              "message": Message,
            }
        }
