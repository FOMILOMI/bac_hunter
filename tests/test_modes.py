from bac_hunter.modes import get_mode_profile


def test_mode_defaults():
    stealth = get_mode_profile("stealth")
    assert stealth.global_rps <= 1.0
    assert stealth.allow_exploitation is False

    std = get_mode_profile("standard")
    assert 1.5 <= std.global_rps <= 2.5

    aggr = get_mode_profile("aggressive")
    assert aggr.allow_exploitation is True

    maxm = get_mode_profile("maximum")
    assert maxm.global_rps >= 5.0
