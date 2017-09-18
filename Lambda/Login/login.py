import requests
import json
import boto3
import datetime
import os
import hashlib

def get_token_auth0(user, password, clientid, db):
    headers = {
        "Content-Type": "application/json"
    }

    url_session = os.environ['urlSessionOauth']

    body = "{" +\
           "\"client_id\":" + " \"" + clientid + "\"," +\
           "\"username\":" + " \"" + user + "\","+"\"password\":" + \
           " \"" + password + "\","+"\"id_token\": \" \"," +\
           "\"connection\":" + " \"" + db + "\"," +\
           "\"grant_type\": \"password\"," + "\"scope\": \"openid\"," +\
           "\"device\":      \" \"" + "}"

    response = requests.post(url_session, data=body, headers=headers)
    return response


def delegation(id_token, clientid):
    headers = {
        "Content-Type": "application/json"
    }

    url_session = os.environ['urlSessionDelegation']

    body = "{" +\
            "\"client_id\":" + " \"" + clientid + "\"," +\
            "\"grant_type\":  \"urn:ietf:params:oauth:grant-type:jwt-bearer\"," +\
            "\"id_token\":" + " \"" + id_token + "\"," +\
            "\"target\":" + " \"" + clientid + "\"," +\
            "\"scope\":  \"openid\"," +\
            "\"api_type\":  \"aws\"" +\
        "}"

    response = requests.post(url_session, data=body, headers=headers)
    return response



def login(username, password, clientid, db):

    # Petition AUTH0
    response = get_token_auth0(user=username, password=password, clientid=clientid, db=db)
    if response.status_code is not 200:
        return response.status_code, response.reason
    j = json.loads(response.text)

    # Delegation

    response2 = delegation(j["id_token"], clientid)
    if response2.status_code is not 200:
        return response2.status_code, response2.reason
    j2 = json.loads(response2.text)
    auth0_token_id = j['id_token']
    print 'Auth0 id_token: '+ auth0_token_id
    aws_secret_key = j2['Credentials']['SecretAccessKey']
    print 'Secret key: '+ aws_secret_key
    aws_access_key = j2['Credentials']['AccessKeyId']
    print 'Access key: '+ aws_access_key
    session_token_aws = j2['Credentials']['SessionToken']
    print 'Session token: '+ session_token_aws
    expiration = j2['Credentials']['Expiration']
    print 'Expirtaion: '+ expiration
    saveUserLogged(username=username, id_token_auth0=auth0_token_id, secret_key=aws_secret_key, access_key=aws_access_key,
                   session_token=session_token_aws, expiration=expiration)
    credentials = {'access_key': aws_access_key, 'secret_key': aws_secret_key, 'session_token':  session_token_aws}
    return credentials

def saveUserLogged(username, id_token_auth0, secret_key, access_key,session_token, expiration):
    """
    This function will save a item in the table users_logged with the information about the login(username, token, date)
    @id_token: Id token belong to AUTH0
    """
    client = boto3.client('dynamodb')
    response = client.put_item(
        TableName=os.environ['tableUsersLogged'],
        Item={
            'Username': {
                'S': username
            },
            'Auth0 token': {
                'S': hashlib.sha1(id_token_auth0).hexdigest()
            },
            'Access Key': {
                'S': hashlib.sha1(access_key).hexdigest()
            },
            'Secret Key': {
                'S': hashlib.sha1(secret_key).hexdigest()
            },
            'Session Token': {
                'S': hashlib.sha1(session_token).hexdigest()
            },
            'Expiration': {
                'S': expiration
            },
            'Date': {
                'S': getDate()
            }
        }
    )
    return response

def getDate():
    return str(datetime.datetime.now()).split()[0]

def handler(event, context):
    if 'role' not in event:
        return "Role not given. should be parent or teacher"

    if 'username' not in event:
        return 'Username not given'

    if 'password' not in event:
        return 'Password not given'

    if event["role"] == "teacher":
        clientid = os.environ['clientIdTeacher']
        db = os.environ['connectionTeacher']
        return login(username=event["username"], password=event["password"], clientid=clientid, db=db)
    if event["role"] == "parent":
        clientid = os.environ['clientIdParent']
        db = os.environ['connectionParent']
        return login(username=event["username"], password=event["password"], clientid=clientid, db=db)

    return "Role not defined"

event = {
  "username": "rdbarrientos",
  "password": "usuario1",
  "role": "parent"
}
print(handler(event=event, context=None))
