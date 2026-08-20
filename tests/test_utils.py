"""The identifier factories -- pure functions, no router involved."""

import uuid

import pytest

from edutap.esc_router_api.utils import ESCN_Factory_Exception
from edutap.esc_router_api.utils import ESI_Factory_Exception
from edutap.esc_router_api.utils import generate_ESCN
from edutap.esc_router_api.utils import generate_ESI


PIC = "123456789"


# --- ESCN ---------------------------------------------------------------------------


def test_an_escn_is_a_version_1_uuid():
    escn = generate_ESCN(pic=PIC)

    assert isinstance(escn, uuid.UUID)
    assert escn.variant == uuid.RFC_4122
    assert escn.version == 1


def test_the_prefix_and_pic_are_readable_in_the_escn():
    """The point of the hexadecimal node: the digits come back out unchanged."""
    assert str(generate_ESCN(pic=PIC))[24:] == "001" + PIC


def test_the_prefix_distinguishes_issuing_servers():
    assert str(generate_ESCN(pic=PIC, prefix=3))[24:] == "003" + PIC


def test_two_escns_from_one_server_differ():
    """Version 1 mixes in a timestamp and a clock sequence, so the node repeating is fine."""
    assert generate_ESCN(pic=PIC) != generate_ESCN(pic=PIC)


@pytest.mark.parametrize("pic", ["1234567890", "12345678", "", "12345678a"])
def test_a_pic_that_is_not_nine_digits_is_refused(pic):
    with pytest.raises(ESCN_Factory_Exception, match="nine digits"):
        generate_ESCN(pic=pic)


@pytest.mark.parametrize("prefix", [1000, 0, -5, 9987])
def test_a_prefix_outside_one_to_999_is_refused(prefix):
    with pytest.raises(ESCN_Factory_Exception, match="between 1 and 999"):
        generate_ESCN(pic=PIC, prefix=prefix)


# --- ESI ----------------------------------------------------------------------------


def test_a_nation_wide_identifier_carries_the_country():
    esi = generate_ESI("nation-wide-scope", student_code="12345", cn="DE")

    assert esi == "urn:schac:personalUniqueCode:int:esi:DE:12345"


def test_a_hei_wide_identifier_carries_the_home_organisation():
    esi = generate_ESI("HEI-wide-scope", student_code="12345", schacHomeOrganization="lmu.de")

    assert esi == "urn:schac:personalUniqueCode:int:esi:lmu.de:12345"


def test_an_unknown_country_code_is_refused():
    with pytest.raises(ESI_Factory_Exception, match="Invalid country code"):
        generate_ESI("nation-wide-scope", student_code="12345", cn="XX")


def test_a_nation_wide_scope_without_a_country_is_refused():
    with pytest.raises(ESI_Factory_Exception, match="needs a country code"):
        generate_ESI("nation-wide-scope", student_code="12345")


def test_a_hei_wide_scope_without_a_home_organisation_is_refused():
    with pytest.raises(ESI_Factory_Exception, match="needs a schacHomeOrganization"):
        generate_ESI("HEI-wide-scope", student_code="12345")


def test_an_over_long_identifier_is_refused():
    """This check used to be an `assert`, and so was absent under `python -O`."""
    with pytest.raises(ESI_Factory_Exception, match="maximum length"):
        generate_ESI("HEI-wide-scope", student_code="x" * 300, schacHomeOrganization="lmu.de")
