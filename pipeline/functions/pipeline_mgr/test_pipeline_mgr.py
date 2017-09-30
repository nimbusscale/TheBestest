#!/usr/bin/env python3
import json
import pytest

from pipeline_mgr import *

@pytest.fixture
def webhook_json():
    with open('test_webhook.json') as test_webhook_file:
        test_webhook = test_webhook_file.read()
    return json.loads(test_webhook)

def test_webhook_handler_valid(webhook_json):
    event = webhook_json
    context = ""
    response = webhook_handler(event, context)
    expected = {
        'pr_info': {
            'owner': 'nimbusscale',
            'repo': 'TheBestest',
            'url': 'https://api.github.com/repos/nimbusscale/TheBestest/pulls/1',
            'title': 'test1',
            'branch': 'webhook_testing',
            'sha': '13d0b21380880d6460dfd5d22ee111d51a5fb684'},
        'action': 'test'
    }
    assert response == expected
