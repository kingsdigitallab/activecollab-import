#!/usr/bin/env python

import urllib2
import json
import requests
import sys
import time
from dateutil.parser import parse
import simplejson

ac_url = "https://app.activecollab.com/148987/api/v1/"
ac_auth_field = "X-Angie-AuthApiToken"


with open('ac_secrets.json.nogit') as f:
        ac_secrets = simplejson.loads(f.read())

ac_key = ac_secrets['ac_token']
ac_company_id = 1 # Temporary while testing
ac_user_id = 2 # Temporary while testing

'''
' Helper function for get calls to activecollab
' 
' Do NOT put a / at the front of the api path
'''
def get_activecollab(api_path, params=None):
    headers = {ac_auth_field: ac_key}
    json_dump = requests.get("{}{}".format(ac_url, api_path), headers=headers).content
    return json.loads(json_dump)


'''
' Helper function for get calls to activecollab
' 
' Do NOT put a / at the front of the api path
'''
def delete_activecollab(api_path):
    headers = {ac_auth_field: ac_key}
    requests.delete("{}{}".format(ac_url, api_path), headers=headers)
    return None


# Get list of projects
projects = get_activecollab('projects')   
for p in projects:
    if not p['id'] == 163:
        delete_activecollab('projects/{}'.format(p['id']))
