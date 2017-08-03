#!/usr/bin/env python3
from get_items import *


def test_lambda_handler():
    event = {'metadata': {'userId': 'jjk3',
                          'requestId': __name__}}
    expected_items = [{'user_id': 'jjk3',
                       'category_name': 'bbq',
                       'place_name': 'central bbq'}]
    response = lambda_handler(event, None)
    assert response['Items'] == expected_items
