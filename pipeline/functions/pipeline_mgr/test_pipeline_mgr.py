#!/usr/bin/env python3
from ast import literal_eval

from pipeline_mgr import *


def test_webhook_handler_valid():
    with open('test_webhook.json') as test_webhook_file:
        test_webhook = test_webhook_file.read()
    webhook_data = literal_eval(test_webhook)
    assert webhook_handler(webhook_data, "")
