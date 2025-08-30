from httpx import HTTPError
from src.edutap.esc_router_api.api_v2 import generate_card_numbers
from src.edutap.esc_router_api.api_v2 import get_card_qr_code
from src.edutap.esc_router_api.api_v2 import get_card_status
from src.edutap.esc_router_api.api_v2 import list_cards
from src.edutap.esc_router_api.models_v2 import CardView

import pytest
import uuid


PIC = "999978433"  # LMU-PIC for Test Purpose


def test_get_all_cards():
    cards = list_cards(size=5)
    assert cards is not None
    assert len(cards) >= 0
    card: CardView
    for card in cards:
        print(card.model_dump_json(indent=2))
        assert card.cardNumber is not None


@pytest.mark.parametrize(
    ["escn", "orientation", "colours", "size"],
    [
        ("25539be8-6423-103e-add8-988999978433", "horizontal", "normal", "XS"),
        ("25539be8-6423-103e-add8-988999978433", "horizontal", "normal", "S"),
        ("25539be8-6423-103e-add8-988999978433", "horizontal", "normal", "M"),
        ("25539be8-6423-103e-add8-988999978433", "horizontal", "inverted", "XS"),
        ("25539be8-6423-103e-add8-988999978433", "horizontal", "inverted", "S"),
        ("25539be8-6423-103e-add8-988999978433", "horizontal", "inverted", "M"),
        ("25539be8-6423-103e-add8-988999978433", "vertical", "normal", "XS"),
        ("25539be8-6423-103e-add8-988999978433", "vertical", "normal", "S"),
        ("25539be8-6423-103e-add8-988999978433", "vertical", "normal", "M"),
        ("25539be8-6423-103e-add8-988999978433", "vertical", "inverted", "XS"),
        ("25539be8-6423-103e-add8-988999978433", "vertical", "inverted", "S"),
        ("25539be8-6423-103e-add8-988999978433", "vertical", "inverted", "M"),
    ],
)
def test_get_card_qr_code_svg(escn: str, orientation: str, colours: str, size: str):
    cr_code = get_card_qr_code(
        escn=escn, orientation=orientation, colours=colours, size=size
    )
    assert cr_code is not None
    with open(f"card-{escn}-{orientation}-{colours}-{size}.svg", "wb") as f:
        f.write(cr_code)


@pytest.mark.parametrize(
    "escn",
    [
        "25539be8-6423-103e-add8-988999978433",
    ],
)
def test_get_card_qr_code_png(escn: str):
    with pytest.raises(ImportError):
        cr_code = get_card_qr_code(escn=escn, Accept="PNG")
        assert cr_code is not None
        with open(f"card-{escn}.png", "wb") as f:
            f.write(cr_code)


@pytest.mark.parametrize(
    "escn",
    [
        "25539be8-6423-103e-add8-988999978433",
    ],
)
def test_get_card_qr_code_text(escn: str):
    cr_code = get_card_qr_code(escn=escn, Accept="TEXT")
    assert cr_code is not None
    with open(f"card-{escn}.txt", "wb") as f:
        f.write(cr_code)


@pytest.mark.parametrize(
    "escn",
    [
        "25539be8-6423-103e-add8-988999978433",
    ],
)
def test_get_card_status(escn: str):
    status = get_card_status(escn=escn)
    assert status is not None
    print(status)


@pytest.mark.parametrize(
    "escn",
    [
        "25539be8-6423-103e-add8-988997978433",
    ],
)
def test_get_card_status_invalid(escn: str):
    with pytest.raises(HTTPError):  # match=f"Card({escn}) not found"):
        status = get_card_status(escn=escn)
        assert status is not None
        print(status)
