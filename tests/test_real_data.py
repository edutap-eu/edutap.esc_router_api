from edutap.esc_router_api.api import get_card_status

import pytest

@pytest.mark.asyncio
async def test_get_card_status():
    status = await get_card_status(escn="024e8a11-e98f-103e-83a9-988999978433")
    assert status is not None
    assert status.cardNumber == "024e8a11-e98f-103e-83a9-988999978433"
    assert status.status == "ACTIVE"
    assert status.expiresAt == "2026-09-30"
    assert status.issuerIdentifier == "999978433"
    assert status.issuerName == "Ludwig-Maximilians-Universität München (LMU)"
    print("\n".join([f"{k}: {v}" for k, v in status.model_dump().items()]))
