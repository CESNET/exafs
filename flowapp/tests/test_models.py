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
        action_id=1,
        expires=datetime.now(),
        user_id=4,
        rstate_id=1
    )
    db.session.add(model)
    db.session.commit()


def test_get_model_if_exists(db):
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

    result = models.get_model_if_exists(models.Flowspec4, form_data, 1)
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
        packet_len="",
        action_id=1,
        expires="123456",
        user_id=1,
        rstate_id=1
    )

    assert model_A != model_B