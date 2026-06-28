import asyncio
from types import SimpleNamespace

from app.services.funnel import FunnelService, FunnelState


def test_ensure_full_access_sets_active():
    user = SimpleNamespace(
        language=None,
        is_channel_subscribed=False,
        is_registered=False,
        registered_at=None,
        is_deposited=False,
        deposited_at=None,
        has_unlimited=False,
        funnel_state=FunnelState.NEW,
    )
    svc = FunnelService(db=None)  # type: ignore[arg-type]
    asyncio.run(svc.ensure_full_access(user))
    assert user.language == "ru"
    assert user.is_channel_subscribed is True
    assert user.is_registered is True
    assert user.is_deposited is True
    assert user.funnel_state == FunnelState.ACTIVE
    assert user.registered_at is not None
    assert user.deposited_at is not None


def test_ensure_full_access_keeps_unlimited():
    user = SimpleNamespace(
        language="en",
        is_channel_subscribed=True,
        is_registered=True,
        registered_at=None,
        is_deposited=False,
        deposited_at=None,
        has_unlimited=True,
        funnel_state=FunnelState.NEW,
    )
    svc = FunnelService(db=None)  # type: ignore[arg-type]
    asyncio.run(svc.ensure_full_access(user))
    assert user.funnel_state == FunnelState.UNLIMITED
