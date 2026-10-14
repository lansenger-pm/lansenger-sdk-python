"""Tests for the 4.6.4.14 authorizationReq message body."""

import pytest

from lansenger_sdk.authorization_requests import authorization_req_payload
from lansenger_sdk.constants import (
    AUTHORIZATION_TYPE_LOCATION,
    MSG_TYPE_AUTHORIZATION_REQ,
)


def test_payload_matches_the_documented_shape():
    assert MSG_TYPE_AUTHORIZATION_REQ == "authorizationReq"
    assert AUTHORIZATION_TYPE_LOCATION == 1
    assert authorization_req_payload() == {"authorizationType": 1}
    assert authorization_req_payload(AUTHORIZATION_TYPE_LOCATION) == {
        "authorizationType": AUTHORIZATION_TYPE_LOCATION
    }


def test_unknown_authorization_type_is_rejected():
    with pytest.raises(ValueError):
        authorization_req_payload(9)
