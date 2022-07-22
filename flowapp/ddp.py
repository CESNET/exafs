from flowapp import db
from flowapp.models import DDPDevice


def get_available_ddos_protector_device() -> DDPDevice:
    """
    Select "the best" device out of available devices, return its REST API and address
    For now, this function only selects the first active DDoS protector in DB
    """
    device = db.session.query(DDPDevice).filter(DDPDevice.active).first()
    return device
