from datetime import datetime

import flowapp.models as models


def test_insert_ipv4(db):
    """
    test the record can be inserted
    :param db: conftest fixture
    :return:
    """
    model = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        packet_len="",
        fragment="",
        action_id=1,
        expires=datetime.now(),
        user_id=4,
        rstate_id=1
    )
    db.session.add(model)
    db.session.commit()


def test_get_ipv4_model_if_exists(db):
    """
    test if the function find existing model correctly
    :param db: conftest fixture
    :return:
    """
    model = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires=datetime.now(),
        user_id=4,
        rstate_id=1
    )
    db.session.add(model)
    db.session.commit()

    form_data = {
        'source': '192.168.1.1',
        'source_mask': '32',
        'source_port': '80',
        'dest': '',
        'dest_mask': '',
        'dest_port': '',
        'protocol': 'tcp',
        'flags': '',
        'packet_len': '',
        'action': 1
    }

    result = models.get_ipv4_model_if_exists(form_data, 1)
    assert result
    assert result == model


def test_get_ipv6_model_if_exists(db):
    """
    test if the function find existing model correctly
    :param db: conftest fixture
    :return:
    """
    model = models.Flowspec6(
        source="2001:0db8:85a3:0000:0000:8a2e:0370:7334",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        next_header="tcp",
        flags="",
        packet_len="",
        action_id=1,
        expires=datetime.now(),
        user_id=4,
        rstate_id=1
    )
    db.session.add(model)
    db.session.commit()

    form_data = {
        'source': '2001:0db8:85a3:0000:0000:8a2e:0370:7334',
        'source_mask': '32',
        'source_port': '80',
        'dest': '',
        'dest_mask': '',
        'dest_port': '',
        'next_header': 'tcp',
        'flags': '',
        'packet_len': '',
        'action': 1
    }

    result = models.get_ipv6_model_if_exists(form_data, 1)
    assert result
    assert result == model


def test_ipv4_eq(db):
    """
    test that creating with valid data returns 201
    """
    model_A = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires="123",
        user_id=4,
        rstate_id=1
    )

    model_B = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires="123456",
        user_id=1,
        rstate_id=1
    )

    assert model_A == model_B


def test_ipv4_ne(db):
    """
    test that creating with valid data returns 201
    """
    model_A = models.Flowspec4(
        source="192.168.2.2",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires="123",
        user_id=4,
        rstate_id=1
    )

    model_B = models.Flowspec4(
        source="192.168.1.1",
        source_mask="32",
        source_port="80",
        destination="",
        destination_mask="",
        destination_port="",
        protocol="tcp",
        flags="",
        fragment="",
        packet_len="",
        action_id=1,
        expires="123456",
        user_id=1,
        rstate_id=1
    )

    assert model_A != model_B



def test_rtbj_eq(db):
    """
    test that two equal rtbh rules are equal
    """
    model_A = models.RTBH(
        ipv4="192.168.1.1",
        ipv4_mask="32",
        ipv6="",
        ipv6_mask="",
        community_id=1,
        expires="123",
        user_id=4,
        rstate_id=1
    )

    model_B = models.RTBH(
        ipv4="192.168.1.1",
        ipv4_mask="32",
        ipv6="",
        ipv6_mask="",
        community_id=1,
        expires="123456",
        user_id=1,
        rstate_id=1
    )

    assert model_A == model_B
