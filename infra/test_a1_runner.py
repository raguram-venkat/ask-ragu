from types import SimpleNamespace as NS

from a1_runner import classify, decide, in_window


def a1(state="RUNNING", ocpus=1.0):
    return NS(lifecycle_state=state, shape_config=NS(ocpus=ocpus))


def test_classify():
    assert classify(500, "InternalError", "Out of host capacity.") == "capacity"
    assert classify(429, "TooManyRequests", "slow down") == "throttled"
    assert classify(503, "ServiceUnavailable", "") == "transient"
    assert classify(400, "QuotaExceeded", "quota ask-ragu-free-tier-guard") == "fatal"
    assert classify(404, "NotAuthorizedOrNotFound", "") == "fatal"


def test_in_window():
    assert in_window(3, "1-6") and not in_window(6, "1-6")
    assert in_window(23, "22-2") and in_window(1, "22-2") and not in_window(12, "22-2")


def test_decide():
    assert decide([], 12, "1-6") == "launch"
    assert decide([a1(), a1()], 12, "1-6") == "fatal"  # never touch a second A1
    assert decide([a1("PROVISIONING")], 12, "1-6") == "wait"
    assert decide([a1("STOPPED")], 12, "1-6") == "start"
    assert decide([a1(ocpus=2.0)], 12, "1-6") == "done"
    assert decide([a1(ocpus=1.0)], 12, "1-6") == "wait"  # outside resize window
    assert decide([a1(ocpus=1.0)], 3, "1-6") == "resize"
