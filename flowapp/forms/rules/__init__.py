"""
Rule forms for the flowapp application.
"""

from .base import IPForm
from .ipv4 import IPv4Form
from .ipv6 import IPv6Form
from .rtbh import RTBHForm
from .whitelist import WhitelistForm

__all__ = [
    "IPForm",
    "IPv4Form",
    "IPv6Form",
    "RTBHForm",
    "WhitelistForm",
]
