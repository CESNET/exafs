from flowapp.messages import format_tcp_flags, format_fragment


# --- format_tcp_flags ---


def test_tcp_flags_v4_single():
    assert format_tcp_flags("SYN", 4) == "tcp-flags SYN;"


def test_tcp_flags_v4_multiple():
    assert format_tcp_flags("SYN ACK FIN", 4) == "tcp-flags SYN ACK FIN;"


def test_tcp_flags_v4_default():
    # default version is 4
    assert format_tcp_flags("SYN ACK") == "tcp-flags SYN ACK;"


def test_tcp_flags_v5_single():
    assert format_tcp_flags("SYN", 5) == "tcp-flags [ syn ];"


def test_tcp_flags_v5_multiple():
    assert format_tcp_flags("SYN ACK FIN", 5) == "tcp-flags [ syn ack fin ];"


def test_tcp_flags_v5_already_lowercase():
    assert format_tcp_flags("syn ack", 5) == "tcp-flags [ syn ack ];"


# --- format_fragment ---


def test_fragment_v4_single():
    assert format_fragment("is-fragment", 4) == "fragment [ is-fragment ];"


def test_fragment_v4_multiple():
    assert format_fragment("is-fragment dont-fragment", 4) == "fragment [ is-fragment dont-fragment ];"


def test_fragment_v4_default():
    assert format_fragment("dont-fragment") == "fragment [ dont-fragment ];"


def test_fragment_v5_is_fragment():
    assert format_fragment("is-fragment", 5) == "fragment [ is-fragment ];"


def test_fragment_v5_dont_fragment():
    assert format_fragment("dont-fragment", 5) == "fragment [ dont-fragment ];"


def test_fragment_v5_not_a_fragment():
    # "not" key maps to "!is-fragment" in IPV4_FRAGMENT_V5
    assert format_fragment("not", 5) == "fragment [ !is-fragment ];"


def test_fragment_v5_unknown_passthrough():
    # unknown values pass through unchanged
    assert format_fragment("first-fragment", 5) == "fragment [ first-fragment ];"
