import socket
import struct


def cidr_to_mask(cidr):
    """
    Returns tuple (masked ip value, mask bits).
    """
    str_ip, str_bits = cidr.split("/")
    ip = dotted_ip_to_int(str_ip)
    bits = int(str_bits)
    assert 0 <= bits < 33
    value = (ip >> bits) << bits
    mask = (0xffffffff >> bits) << bits
    return value, mask


def dotted_ip_to_int(addr):
    net = socket.inet_aton(addr)
    return struct.unpack(">L", net)[0]


def matches_cidr(addr, cidr):
    value, mask = cidr_to_mask(cidr)
    try:
        ip = dotted_ip_to_int(addr)
    except socket.error:
        return False
    return (ip & mask) == value


def is_multicast(addr):
    return matches_cidr(addr, "224.0.0.0/28")


def make_mreq(addr):
    """
    Creates new ip_mreq struct with given IP address.
    """
    net = socket.inet_aton(addr)
    return struct.pack("4sl", net, socket.INADDR_ANY)


def join_multicast_group(sock, addr):
    """
    > join_multicast_group(sock, "239.0.0.1")
    """
    mreq = make_mreq(addr)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)


def leave_multicast_group(sock, addr):
    """
    > leave_multicast_group(sock, "239.0.0.1")
    """
    mreq = make_mreq(addr)
    sock.setsockopt(socket.IPPROTO_IP, socket.IP_DROP_MEMBERSHIP, mreq)


def make_udp_server_socket(addr, port):
    """
    Makes non-blocking UDP socket, which binds to destination
    address addr and port.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((addr, port))
    sock.setblocking(0)
    return sock


def make_multicast_server_socket(ip_addr, port):
    """
    Makes non-blocking UDP socket, which binds to destination multicast
    address and port, and joins multicast group.
    """
    sock = make_udp_server_socket(ip_addr, port)
    join_multicast_group(sock, ip_addr)
    return sock
