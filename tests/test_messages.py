import flowapp.models as models
from flowapp.constants import ANNOUNCE
from flowapp.messages import format_tcp_flags, format_fragment, create_rtbh


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


class TestCreateRtbh:
    def test_as_path_match_found(self, app, db):
        """create_rtbh includes as-path string when ASPath record matches the source IP."""
        # Create a community with as_path enabled
        community = models.Community(
            name="test-aspath-comm",
            comm="65535:65283",
            larcomm="",
            extcomm="",
            description="",
            as_path=True,
            role_id=2,
        )
        db.session.add(community)

        # Create an ASPath record matching the RTBH source
        aspath = models.ASPath()
        aspath.prefix = "147.230.1.99/32"
        aspath.as_path = "64512 64513"
        db.session.add(aspath)
        db.session.commit()

        rule = models.RTBH(
            ipv4="147.230.1.99",
            ipv4_mask=32,
            ipv6="",
            ipv6_mask=0,
            community_id=community.id,
            expires=None,
            user_id=1,
            org_id=1,
            rstate_id=1,
        )
        db.session.add(rule)
        db.session.commit()

        msg = create_rtbh(rule, ANNOUNCE)
        assert "as-path [ 64512 64513 ]" in msg

    def test_as_path_no_match(self, app, db):
        """create_rtbh omits as-path string when no ASPath record matches."""
        community = models.Community(
            name="test-aspath-comm-nomatch",
            comm="65535:65283",
            larcomm="",
            extcomm="",
            description="",
            as_path=True,
            role_id=2,
        )
        db.session.add(community)
        db.session.commit()

        rule = models.RTBH(
            ipv4="10.0.0.1",
            ipv4_mask=32,
            ipv6="",
            ipv6_mask=0,
            community_id=community.id,
            expires=None,
            user_id=1,
            org_id=1,
            rstate_id=1,
        )
        db.session.add(rule)
        db.session.commit()

        msg = create_rtbh(rule, ANNOUNCE)
        assert "as-path" not in msg

    def test_no_as_path_community(self, app, db):
        """create_rtbh skips DB query entirely when community.as_path is False."""
        community = models.Community(
            name="test-no-aspath-comm",
            comm="65535:65283",
            larcomm="",
            extcomm="",
            description="",
            as_path=False,
            role_id=2,
        )
        db.session.add(community)
        db.session.commit()

        rule = models.RTBH(
            ipv4="147.230.2.1",
            ipv4_mask=32,
            ipv6="",
            ipv6_mask=0,
            community_id=community.id,
            expires=None,
            user_id=1,
            org_id=1,
            rstate_id=1,
        )
        db.session.add(rule)
        db.session.commit()

        msg = create_rtbh(rule, ANNOUNCE)
        assert "as-path" not in msg
