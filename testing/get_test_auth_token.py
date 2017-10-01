#!/usr/bin/env python3
"""Gets an auth token for the test user, creates test user if need be."""
import boto3

# Todo Parametrize
stackname = 'thebestest-stack'
test_username = "test123"
test_password = "test123"

def get_cognito_info(cfn_stackname):
    """Gets Cognito info from stack outputs"""
    cfn_stack = cloudformation.Stack(cfn_stackname)
    for output in cfn_stack.outputs:
        if output['OutputKey'] == 'UserPoolId':
            userpool_id = output['OutputValue']
        elif output['OutputKey'] == 'AdminClientId':
            adminclient_id = output['OutputValue']
    return {'userpool_id': userpool_id, 'adminclient_id': adminclient_id}


def check_user_exists(username, cognito_info):
    """Returns true if user exists or false if doesn't exist"""
    cognito_reposnse = cognito.list_users(
        UserPoolId=cognito_info['userpool_id'],
        Filter="username = '{}'".format(username)
    )
    if len(cognito_reposnse['Users']) > 0:
        return True
    else:
        return False

def signup_test_user(username, password, cognito_info):
    """signs up and confirms a test user"""
    cognito.sign_up(ClientId=cognito_info['adminclient_id'],
                    Username=test_username,
                    Password=test_password)
    cognito.admin_confirm_sign_up(UserPoolId=cognito_info['userpool_id'],
                                  Username=test_username)

def get_auth_token(username, password, cognito_info):
    """Returns Auth token for user"""
    login_response = cognito.admin_initiate_auth(
        UserPoolId=cognito_info['userpool_id'],
        ClientId=cognito_info['adminclient_id'],
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={ 'USERNAME': username, 'PASSWORD': password}
    )
    return login_response['AuthenticationResult']['IdToken']


if __name__ == '__main__':
    cloudformation = boto3.resource('cloudformation')
    cognito = boto3.client('cognito-idp')
    cognito_info = get_cognito_info(stackname)
    if check_user_exists(test_username, cognito_info) is False:
        signup_test_user(test_username, test_password, cognito_info)
    print(get_auth_token(test_username, test_password, cognito_info))




