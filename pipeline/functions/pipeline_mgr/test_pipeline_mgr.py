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
    assert webhook_handler(event, context)
