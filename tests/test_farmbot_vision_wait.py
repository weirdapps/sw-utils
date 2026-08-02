from farmbot import vision
from farmbot.vision import Match


def test_wait_for_returns_match_when_it_appears():
    responses = [None, None, Match(1, 2, 0.99)]
    calls = {"n": 0}
    def finder(screen, template, threshold):
        r = responses[calls["n"]]
        calls["n"] += 1
        return r
    clock_vals = iter([0.0, 0.0, 0.1, 0.2, 0.3])
    m = vision.wait_for(lambda: object(), object(), timeout=5.0, interval=0.01,
                        finder=finder, clock=lambda: next(clock_vals), sleeper=lambda s: None)
    assert m == Match(1, 2, 0.99)
    assert calls["n"] == 3


def test_wait_for_times_out_to_none():
    clock_vals = iter([0.0, 1.0, 2.0, 11.0])
    m = vision.wait_for(lambda: object(), object(), timeout=10.0, interval=0.01,
                        finder=lambda *a: None, clock=lambda: next(clock_vals), sleeper=lambda s: None)
    assert m is None
