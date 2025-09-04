from edutap.esc_router_api.api import get_card_qr_code
from edutap.esc_router_api.api import get_card_status
from edutap.esc_router_api.api import list_cards
from edutap.esc_router_api.models import CardView
from httpx import HTTPError

import pytest


PIC = "999978433"  # LMU-PIC for Test Purpose


@pytest.mark.asyncio
async def test_get_all_cards():
    cards = await list_cards(size=0)
    assert cards is not None
    assert len(cards) >= 0
    card: CardView
    for card in cards:
        print(card.model_dump_json(indent=2))
        assert card.cardNumber is not None


@pytest.mark.asyncio
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
async def test_get_card_qr_code_svg(escn: str, orientation: str, colours: str, size: str):
    cr_code = await get_card_qr_code(escn=escn, orientation=orientation, colours=colours, size=size)
    assert cr_code is not None
    with open(f"card-{escn}-{orientation}-{colours}-{size}.svg", "wb") as f:
        f.write(cr_code)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "escn",
    [
        "25539be8-6423-103e-add8-988999978433",
    ],
)
async def test_get_card_qr_code_png(escn: str):
    with pytest.raises(Exception):
        cr_code = await get_card_qr_code(escn=escn, Accept="PNG")
        assert cr_code is not None
        with open(f"card-{escn}.png", "wb") as f:
            f.write(cr_code)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "escn",
    [
        "25539be8-6423-103e-add8-988999978433",
    ],
)
async def test_get_card_qr_code_text(escn: str):
    cr_code = await get_card_qr_code(escn=escn, Accept="TEXT")
    assert cr_code is not None
    with open(f"card-{escn}.txt", "wb") as f:
        f.write(cr_code)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "escn",
    [
        "25539be8-6423-103e-add8-988999978433",
    ],
)
async def test_get_card_status(escn: str):
    status = await get_card_status(escn=escn)
    assert status is not None
    print(status)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "escn",
    [
        "25539be8-6423-103e-add8-988997978433",
    ],
)
async def test_get_card_status_invalid(escn: str):
    with pytest.raises(HTTPError):  # match=f"Card({escn}) not found"):
        status = await get_card_status(escn=escn)
        assert status is not None
        print(status)
