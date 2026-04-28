import os
import socket
import struct
import sys
import time

from sfkit.api import get_doc_ref_dict, get_username, update_firestore
from sfkit.utils import constants
from sfkit.utils.helper_functions import authenticate_user

MAX_PARTICIPANTS = 10
MAX_THREADS = 100


def setup_networking(ports_str: str = "", ip_address: str = "", **kwargs) -> None:
    print("Setting up networking...")
    print(
        "NOTE: this step should be run after all participants have joined the study.  If you run this step before all participants have joined, you will need to re-run this step after all participants have joined."
    )

    # Test NAT connectivity
    if not ip_address:
        while not ip_address:
            nat_type, ip_address, _ = get_ip_info(stun_host="stun.l.google.com", stun_port=19302) # from sfkit-proxy
            time.sleep(1)

        if constants.SFKIT_PROXY_ON:
            if nat_type.startswith("Symmetric"):
                print(
                    "Error: Symmetric NAT detected. This type of NAT is not supported when SFKIT_PROXY_ON=true."
                )
                print(
                    "Please use a different network or configure your network to use a different NAT type."
                )
                sys.exit(1)
            print(f"NAT type: {nat_type}")

            # internal ip address
            ip_address = socket.gethostbyname(socket.gethostname())
            print("Using internal ip address:", ip_address)
        else:  # external ip address
            print("Using external ip address:", ip_address)

    authenticate_user()
    doc_ref_dict: dict = get_doc_ref_dict()
    role: int = doc_ref_dict["participants"].index(get_username())

    print("Processing...")
    update_firestore(f"update_firestore::IP_ADDRESS={ip_address}")

    if ports_str:
        [validate_port(port) for port in ports_str.split(",")]
        # pad ports_str with nulls if necessary
        pad_length = len(doc_ref_dict["participants"]) - len(ports_str.split(","))
        if pad_length < 0:
            print(
                "WARNING: You have provided more ports than there are participants.  The extra ports will be ignored."
            )
            ports_str = ",".join(
                ports_str.split(",")[: len(doc_ref_dict["participants"])]
            )
        ports_str = "null," * pad_length + ports_str
    elif doc_ref_dict["study_type"] == "SF-RELATE":
        default = ["null,3110,7320", "null,null,9210", "null,null,null"]
        ports_str = default[role]
    else:
        base = 8100 + MAX_PARTICIPANTS * MAX_THREADS * role
        ports = [
            base + MAX_THREADS * r for r in range(len(doc_ref_dict["participants"]))
        ]
        ports_str = ",".join([str(p) for p in ports])

    update_firestore(f"update_firestore::PORTS={ports_str}")
    print("Successfully communicated networking information!")


def validate_port(port: str) -> str:
    if port.isdigit() and 1024 <= int(port) <= 65535:
        return port
    print(
        f"{port} is an invalid port number.  Please enter a number between 1024 and 65535."
    )
    exit(1)

# RFC 5389 STUN constants
_STUN_MAGIC = 0x2112A442
_STUN_BINDING_REQUEST = 0x0001
_ATTR_MAPPED_ADDRESS = 0x0001
_ATTR_XOR_MAPPED_ADDRESS = 0x0020

# Secondary STUN servers used to probe NAT mapping behavior. The primary server
# (caller-supplied stun_host) plus these are queried on the SAME socket; if all
# return the same external (ip, port), the NAT does Endpoint-Independent Mapping
# (RFC 4787 REQ-1). Otherwise the mapping is per-destination ("symmetric").
_SECONDARY_STUN_SERVERS = (
    ("stun.cloudflare.com", 3478),
    ("stun.stunprotocol.org", 3478),
    ("stun.nextcloud.com", 443),
    ("stun.sipgate.net", 3478),
)


def _stun_query(sock: socket.socket, server: tuple) -> tuple | None:
    """Send a STUN Binding Request and return the reflexive (ip, port), or None on failure."""
    txid = os.urandom(12)
    req = struct.pack(">HHI12s", _STUN_BINDING_REQUEST, 0, _STUN_MAGIC, txid)
    try:
        sock.sendto(req, server)
        data, _ = sock.recvfrom(1500)
    except (socket.gaierror, socket.timeout, OSError):
        return None
    if len(data) < 20:
        return None
    _, mlen, _, _ = struct.unpack(">HHI12s", data[:20])
    pos = 20
    while pos + 4 <= 20 + mlen and pos + 4 <= len(data):
        atype, alen = struct.unpack(">HH", data[pos : pos + 4])
        val = data[pos + 4 : pos + 4 + alen]
        pos += 4 + ((alen + 3) & ~3)
        if atype == _ATTR_XOR_MAPPED_ADDRESS and len(val) >= 8 and val[1] == 0x01:
            port = struct.unpack(">H", val[2:4])[0] ^ (_STUN_MAGIC >> 16)
            ip = socket.inet_ntoa(
                struct.pack(">I", struct.unpack(">I", val[4:8])[0] ^ _STUN_MAGIC)
            )
            return (ip, port)
        if atype == _ATTR_MAPPED_ADDRESS and len(val) >= 8 and val[1] == 0x01:
            port = struct.unpack(">H", val[2:4])[0]
            ip = socket.inet_ntoa(val[4:8])
            return (ip, port)
    return None


def get_ip_info(
    source_ip: str = "0.0.0.0",
    source_port: int = 54320,
    stun_host: str | None = None,
    stun_port: int = 3478,
) -> tuple:
    """Determine NAT mapping behavior using RFC 5389 STUN Binding Requests on a single socket.

    Returns (nat_type, external_ip, external_port) where nat_type is one of:
      - "Blocked"                       primary STUN server unreachable
      - "Symmetric NAT"                 mapping differs across destinations (no EIM)
      - "Endpoint-Independent Mapping"  same external (ip, port) across all responding secondaries
      - "Inconclusive"                  primary worked but no secondary responded

    Only mapping behavior (RFC 4787 §4.1) is tested; filtering behavior is not.
    """
    primary = (stun_host or "stun.l.google.com", stun_port)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(3)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        s.bind((source_ip, source_port))
        primary_result = _stun_query(s, primary)
        if primary_result is None:
            return ("Blocked", None, None)
        ext_ip, ext_port = primary_result
        confirmations = 0
        for srv in _SECONDARY_STUN_SERVERS:
            r = _stun_query(s, srv)
            if r is None:
                continue
            if r != primary_result:
                return ("Symmetric NAT", ext_ip, ext_port)
            confirmations += 1
            if confirmations >= 2:
                return ("Endpoint-Independent Mapping", ext_ip, ext_port)
        if confirmations == 0:
            return ("Inconclusive", ext_ip, ext_port)
        return ("Endpoint-Independent Mapping", ext_ip, ext_port)
    finally:
        s.close()
