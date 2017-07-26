#!/usr/bin/env python3
from get_items_by_user import *


def test_lambda_handler():
    event = {'user_id': 'jjk3'}
    expected_items = [{'user_id': 'jjk3',
                       'category_name': 'bbq',
                       'place_name': 'central bbq'}]
    response = lambda_handler(event, None)
    assert response['Items'] == expected_items
