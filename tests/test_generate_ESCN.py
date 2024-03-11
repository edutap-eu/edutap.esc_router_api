from edutap.esc_router_api.utils import ESCN_Factory_Exception
from edutap.esc_router_api.utils import generate_ESCN

import pytest
import uuid


def test_generate_ESCN():
    PIC = "999978433"

    escn = generate_ESCN(pic=PIC)
    assert isinstance(escn, uuid.UUID)
    assert escn.variant == uuid.RFC_4122
    assert escn.version == 1
    assert str(escn)[24:] == "001" + PIC


def test_generate_ESCN_with_prefix():
    PIC = "999978433"
    PREFIX = 3

    escn = generate_ESCN(pic=PIC, prefix=PREFIX)
    assert isinstance(escn, uuid.UUID)
    assert str(escn)[24:] == "003" + PIC


def test_generate_ESCN__invalid_PIC():
    PIC = "1234567890"

    with pytest.raises(ESCN_Factory_Exception):
        generate_ESCN(pic=PIC)
