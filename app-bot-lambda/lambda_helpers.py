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
import urllib
import io

# --- Helpers that build all of the responses ---
def elicit_intent(intent, activeContexts, sessionAttributes, message, requestAttributes):
    return { 
        'messages': [message],
        'requestAttributes': requestAttributes,
        'sessionState': {
            'activeContexts': activeContexts,
            'intent': intent,
            'sessionAttributes': sessionAttributes,
            'dialogAction': {
                'type': 'ElicitIntent'
            }
        }
    }
    
def elicit_slot(intent, activeContexts, sessionAttributes, slot, message, requestAttributes):
    return { 
        'messages': [message],
        'requestAttributes': requestAttributes,
        'sessionState': {
            'activeContexts': activeContexts,
            'intent': intent,
            'sessionAttributes': sessionAttributes,
            'dialogAction': {
                'slotToElicit': slot,
                'type': 'ElicitSlot'
            }
        }
    }

def close(intent, activeContexts, sessionAttributes, message, requestAttributes):
    return { 
        'messages': [message],
        'requestAttributes': requestAttributes,
        'sessionState': {
            'activeContexts': activeContexts,
            'intent': intent,
            'sessionAttributes': sessionAttributes,
            'dialogAction': {
                'type': 'Close'
            }
        }
    }

def delegate(intent, activeContexts, sessionAttributes, messages, requestAttributes):
    return { 
        'messages': messages,
        'requestAttributes': requestAttributes,
        'sessionState': {
            'activeContexts': activeContexts,
            'intent': intent,
            'sessionAttributes': sessionAttributes,
            'dialogAction': {
                'type': 'Delegate'
            }
        }
    }
    
def confirm_intent(intent, activeContexts, sessionAttributes, message, requestAttributes):
    return { 
        'messages': [message],
        'requestAttributes': requestAttributes,
        'sessionState': {
            'activeContexts': activeContexts,
            'intent': intent,
            'sessionAttributes': sessionAttributes,
            'dialogAction': {
                'type': 'ConfirmIntent'
            }
        }
    }
    
    
def listpicker_template(elements, title):
    template = {
        "templateType": "ListPicker",
        "version": "1.0",
        "data": {
            "replyMessage": {
                "title": "Thanks for selecting!"
            },
            "content": {
                "title": title,
                "subtitle": "Tap to select option",
                "elements": elements
            }
        }
    }
   
    return template


def get_urlfile_bytes(urlfile):
    with urllib.request.urlopen(urlfile) as imagefile:
        imagebytes = bytes(imagefile.read())
    return imagebytes