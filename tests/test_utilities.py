from edutap.esc_router_api.api import generate_card_numbers

import pytest
import uuid


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
        assert uuid.UUID(escn)  # is valid UUID
        assert str(escn).endswith(f"001{PIC}")
        print(escn)


@pytest.mark.asyncio
async def test_generate_card_numbers_zero():
    escns = await generate_card_numbers(pic=PIC, prefix=1, numberOfESCN=0)
    assert escns is not None
    assert isinstance(escns, list)
    assert len(escns) == 0


@pytest.mark.asyncio
async def test_generate_card_numbers_more_than_hundred():
    with pytest.raises(Exception):
        escns = await generate_card_numbers(pic=PIC, prefix=1, numberOfESCN=101)
        assert escns is None


@pytest.mark.asyncio
async def test_generate_large_set_of_card_numbers():
    escns = set()
    for index in range(10_000):
        result = await generate_card_numbers(pic=PIC, prefix=1, numberOfESCN=100)
        escns.update(result)
    assert escns is not None
    assert isinstance(escns, set)
    assert len(escns) == 1_000_000  # all unique
    for escn in escns:
        # assert isinstance(escn, uuid.UUID)
        assert uuid.UUID(escn)  # is valid UUID
        assert str(escn).endswith(f"001{PIC}")
