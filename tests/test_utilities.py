import pytest

import uuid
from edutap.esc_router_api.api_v2 import generate_card_numbers


PIC = "999978433"  # LMU-PIC for Test Purpose


@pytest.mark.asyncio
async def test_generate_card_numbers():
    escns = await generate_card_numbers(pic=PIC, prefix=1, numberOfESCN=20)
    assert escns is not None
    assert isinstance(escns, list)
    assert len(escns) == 20
    assert len(set(escns)) == 20  # all unique
    for escn in escns:
        # assert isinstance(escn, uuid.UUID)
        assert str(escn).endswith(f"001{PIC}")
        print(escn)




@pytest.mark.asyncio
async def test_generate_large_set_of_card_numbers():
    escns = await generate_card_numbers(pic=PIC, prefix=1, numberOfESCN=1_000_000)
    assert escns is not None
    assert isinstance(escns, list)
    assert len(escns) == 1_000_000
    assert len(set(escns)) == 1_000_000  # all unique
    for escn in escns:
        # assert isinstance(escn, uuid.UUID)
        assert str(escn).endswith(f"001{PIC}")
        print(escn)