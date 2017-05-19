#!/usr/bin/env python

import urllib2
import json
import requests
import sys
import time
from dateutil.parser import parse
import pprint
import os
import simplejson

ac_url = "https://app.activecollab.com/148987/api/v1/"
ac_auth_field = "X-Angie-AuthApiToken"

with open('ac_secrets.json.nogit') as f:
        ac_secrets = simplejson.loads(f.read())

ac_key = ac_secrets['ac_token']

ac_company_id = 1 # Temporary while testing
ac_user_id = 2 # Temporary while testing
ac_template_id = 6 # Template ID to use when importing

with open('trello_secrets.json.nogit') as f:
        trello_secrets = simplejson.loads(f.read())
        
trello_key = trello_secrets['key']
trello_token = trello_secrets['token']

trello_url = "https://api.trello.com/1/"
trello_auth = "?key={}&token={}".format(trello_key, trello_token)

trello_board_id = "56bc9721d9760474a03e7ead"


print "#####################"
print "Importing from trello"
print "##################### \n"

print "Using key: {}".format(trello_key)
print "Using token: {} \n".format(trello_token)


print "#####################"
print "Important Note"
print "#####################"

print "Users & Labels should already have been created\n"

'''
' Defines a quick helper function to help with GET api calls to trello
' 
' Do NOT put a / at the front of the api path
'''
def get_trello(api_path, params=None):
    query_string = "" # Blank query string to start!
    if params:
        for key, value in params.iteritems():
            query_string = "{}&{}={}".format(query_string, key, value)
    json_dump = urllib2.urlopen("{}{}{}{}".format(trello_url, api_path, trello_auth, query_string)).read()
    return json.loads(json_dump)


'''
' Helper function for post calls to activecollab
' 
' Do NOT put a / at the front of the api path
'''
def post_activecollab(api_path, params=None):
    headers = {ac_auth_field: ac_key, "Content-Type": "application/json"}
    json_dump = requests.post("{}{}".format(ac_url, api_path), data=json.dumps(params), headers=headers).content
    return json.loads(json_dump)

'''
' Helper function for batch post calls to activecollab
' We only use a single file (it only supports that!)
' 
' Do NOT put a / at the front of the api path
'''
def batch_activecollab(api_path, params=None):
    headers = {ac_auth_field: ac_key, "Content-Type": "application/json"}
    json_dump = requests.post("{}{}".format(ac_url, api_path), data=json.dumps(params), headers=headers).content
    json_dump = json_dump.replace("[", "")
    json_dump = json_dump.replace("]", "")   
    return json.loads(json_dump)



'''
' Helper function for upload calls to activecollab
' 
' Do NOT put a / at the front of the api path
'''
def upload_activecollab(files=None):
    headers = {ac_auth_field: ac_key}
    json_dump = requests.post("{}upload-files".format(ac_url), files=files, headers=headers).content
    json_dump = json_dump.replace("[", "")
    json_dump = json_dump.replace("]", "")
    return json.loads(json_dump)


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
' Helper function for put calls to activecollab
' 
' Do NOT put a / at the front of the api path
'''
def put_activecollab(api_path, params=None):
    headers = {ac_auth_field: ac_key, "Content-Type": "application/json"}
    json_dump = requests.put("{}{}".format(ac_url, api_path), data=json.dumps(params), headers=headers).content
    return json.loads(json_dump)

'''
' Defines a helper function to check if a user wants to 
' proceed with an object.
'''
def check_proceed(object_name=None):
    if object_name:
        print "Do you want to import {}? Y/N:".format(object_name)
    else:
        print "Do you want to import this object? Y/N:"
    return sys.stdin.readline().splitlines()[0].lower() == "y"

'''
' Let's do this!
'''

# Get lists under the project board 
trello_lists = get_trello("boards/{}/lists".format(trello_board_id))

users = {}

users['58988f56f09d6ad85d0aba79'] = '22'
users['58b2c4b65410e43e7bf39b56'] = '2'
users['57d7df1199fd343291835519'] = '30'
users['56cb30cc88e4a79076ab7caa'] = '20'
users['5818b75ed9a14d529edced33'] = '23'
users['56cb3457bed63e65d797bfe2'] = '26'
users['4e72d39a6b02eb0000270ca1'] = '27'
users['4f70cecf0790492248b29bb1'] = '1'
users['5731b54213174fac1b9af04c'] = '28'
users['56b85d2c26ea671b15d07110'] = '25'
users['58c692c36de567acb36de4e2'] = '29'
users['57f2711f58308031a56c0c10'] = '19'
users['5139ed2c1d1044f86b0036b3'] = '31'
users['56a8b1907f0e962f696c7f04'] = '24'

# If user doesn't exist, assign it to miguel ;)
def get_user(uid):
    try:
        return users[uid]
    except:
        return '36'

for trello_list in trello_lists:
    list_name = trello_list['name'].upper()
    list_id = trello_list['id']

    # Check if we want to import a list
    if check_proceed("list {}".format(list_name)):

        print "Importing {}".format(list_name)

        ac_list_id = None

        # Get the AC list (well, label) ID
        ac_lists = get_activecollab('labels/project-labels')
        for l in ac_lists:
            if l['name'] == list_name:
                ac_list_id = l['id']

     
        # Get cards under list
        trello_cards = get_trello("lists/{}/cards".format(list_id))


        for trello_card in trello_cards:
            card_id = trello_card['id'].encode('utf-8')
            card_name = trello_card['name'].encode('utf-8')
            card_description = trello_card['desc'].encode('utf-8').split("---\n[Elegantt")[0].replace("[", "").replace("]", "")
            
            # ignore templates card
            if card_name == 'TEMPLATES':
                continue

            print " - Importing project/card {}".format(card_name)
            
            card_vars = { "name": card_name, "company_id": ac_company_id, "leader_id": ac_user_id, "label_id" : ac_list_id, "body" : card_description, "template_id" : ac_template_id }
            
            ac_card_id = post_activecollab('projects', card_vars)['single']['id']

            
            # Only want comments
            trello_card_actions = get_trello("cards/{}/actions".format(card_id))

            if trello_card_actions:
                # Reverse the list
                trello_card_actions = trello_card_actions[::-1]

                # Create a discussion:
                discussion_vars = { "name" : "Trello comments" }
                discussion = post_activecollab("/projects/{}/discussions".format(ac_card_id), discussion_vars)
                ac_discussion_id = discussion['single']['id']


                for trello_action in trello_card_actions:
                    if trello_action['type'] == 'commentCard': 
                        action_text = trello_action['data']['text']
                        action_uid = trello_action['idMemberCreator']
                        action_uid = get_user(action_uid)
                        
                        action_date = trello_action['date']
                        action_date = int(time.mktime(parse(action_date).timetuple()))

                        comment_vars = { "body" : action_text, "created_by_id" : action_uid, "updated_by_id" : action_uid }
                        
                        comment_id = post_activecollab('/comments/discussion/{}'.format(ac_discussion_id), comment_vars)['single']['id']

                        put_activecollab('comments/{}'.format(comment_id), { "created_on" : action_date, "created_by_id" : action_uid, "updated_by_id" : action_uid })
                        put_activecollab('comments/{}'.format(comment_id), { "updated_on" : action_date , "created_by_id" : action_uid, "updated_by_id" : action_uid})
            
            # Attachments - aws or gdrive.
            # BIG warning: This google drive API is ***UNDOCUMENTED***
            # and was reverse engineered by me in an afternoon. Don't trust
            # it with your life.
            trello_card_attachments = get_trello("cards/{}/attachments".format(card_id))
            for trello_attachment in trello_card_attachments:
                attachment_name = trello_attachment['name']
                attachment_url = trello_attachment['url']
                if 'google.com' in attachment_url:
                    drive_file = {  
                       "docs":[  
                          {  
                             "serviceId":"doc",
                             "mimeType":"application/vnd.google-apps.document",
                             "name": attachment_name,
                             "description":"",
                             "type":"document",
                             "iconUrl":"https://drive-thirdparty.googleusercontent.com/16/type/application/vnd.google-apps.document",
                             "url": attachment_url,
                             "embedUrl": attachment_url,
                             "driveSuccess":"true",
                             "sizeBytes":0,
                             "isShared":"true",
                             "code":"tka56vzzcvc"
                          }
                       ]
                    }
                    
                    drive_file_code = batch_activecollab('integrations/google-drive/batch', drive_file)['code']
                    
                    drive_move = {
                        "file_01": drive_file_code,
                        "is_hidden_from_clients":"false"
                    }
                    
                    post_activecollab('projects/{}/files/batch'.format(ac_card_id), drive_move)
                    
                
                elif 'amazonaws.com' in attachment_url:
                    # Upload file to /upload-files, with the file in the "file" key.
                    # This seems to accept a multipart request
                    print " - - Copying: {} from {}".format(attachment_name, attachment_url)
                    filename = attachment_name.split("/")[-1]
                    r = requests.get(attachment_url)
                    with open("attachments/{}".format(filename), "wb") as aws_file:
                        aws_file.write(r.content)

                    aws_file = {'file': open("attachments/{}".format(filename), 'rb')}
                    upload = upload_activecollab(aws_file)
                    aws_file_code = upload['code']

                    aws_move = {
                        "file_01": aws_file_code,
                        "is_hidden_from_clients":"false"
                    }

                    try:
                        os.remove("attachments/{}".format(filename))
                    except:
                        pass
                    post_activecollab('projects/{}/files/batch'.format(ac_card_id), aws_move)
            
