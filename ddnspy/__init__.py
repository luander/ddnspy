__version__ = '0.1.0'

from ddnspy import (
    ddns,
    dns
)
from ddnspy.providers import cf

assert(cf)
assert(ddns)
assert(dns)