# -*- coding: utf-8 -*-
import socket,os,re

def reply_to_iplist(data):
    assert isinstance(data, basestring)
    iplist = ['.'.join(str(ord(x)) for x in s) for s in re.findall('\xc0.\x00\x01\x00\x01.{6}(.{4})', data) if all(ord(x) <= 255 for x in s)]
    return iplist

def domain_to_ip(dnsserver,domain):
    dnsserver = dnsserver
    seqid = os.urandom(2)
    host = ''.join(chr(len(x))+x for x in domain.split('.'))
    data = '%s\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00%s\x00\x00\x01\x00\x01' % (seqid, host)
    sock = socket.socket(socket.AF_INET,type=socket.SOCK_DGRAM)
    sock.settimeout(20)
    sock.sendto(data, (dnsserver, 53))
    data = sock.recv(512)
    return reply_to_iplist(data)

print domain_to_ip("8.8.8.8","www.baidu.com")
