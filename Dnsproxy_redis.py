#!/usr/bin/env python
# -*- coding: utf-8 -*-
import SocketServer
import struct
import socket as socketlib
import redis
import socket
import os
import re

class query_DNS:

    @staticmethod
    def domain_to_ip(dnsserver,domain):
        seqid = os.urandom(2)
        host = ''.join(chr(len(x))+x for x in domain.split('.'))
        data = '%s\x01\x00\x00\x01\x00\x00\x00\x00\x00\x00%s\x00\x00\x01\x00\x01' % (seqid, host)
        sock = socket.socket(socket.AF_INET,type=socket.SOCK_DGRAM)
        sock.settimeout(20)
        sock.sendto(data, (dnsserver, 53))
        data = sock.recv(512)
        assert isinstance(data, basestring)
        iplist = ['.'.join(str(ord(x)) for x in s) for s in re.findall('\xc0.\x00\x01\x00\x01.{6}(.{4})', data) if all(ord(x) <= 255 for x in s)]
        return iplist

class SinDNSQuery:
    def __init__(self, data):
        i = 1
        self.name = ''
        while True:
            d = ord(data[i])
            if d == 0:
                break;
            if d < 32:
                self.name = self.name + '.'
            else:
                self.name = self.name + chr(d)
            i = i + 1
        self.querybytes = data[0:i + 1]
        (self.type, self.classify) = struct.unpack('>HH', data[i + 1:i + 5])
        self.len = i + 5
    def getbytes(self):
        return self.querybytes + struct.pack('>HH', self.type, self.classify)

class SinDNSAnswer:
    def __init__(self, ip):
        self.name = 49164
        self.type = 1
        self.classify = 1
        self.timetolive = 190
        self.datalength = 4
        self.ip = ip
    def getbytes(self):
        res = struct.pack('>HHHLH', self.name, self.type, self.classify, self.timetolive, self.datalength)
        s = self.ip.split('.')
        res = res + struct.pack('BBBB', int(s[0]), int(s[1]), int(s[2]), int(s[3]))
        return res

class SinDNSFrame:
    def __init__(self, data):
        (self.id, self.flags, self.quests, self.answers, self.author, self.addition) = struct.unpack('>HHHHHH', data[0:12])
        self.query = SinDNSQuery(data[12:])
    def getname(self):
        return self.query.name
    def setip(self, ip):
        self.answer = SinDNSAnswer(ip)
        self.answers = 1
        self.flags = 33152
    def getbytes(self):
        res = struct.pack('>HHHHHH', self.id, self.flags, self.quests, self.answers, self.author, self.addition)
        res = res + self.query.getbytes()
        if self.answers != 0:
            res = res + self.answer.getbytes()
        return res

class SinDNSUDPHandler(SocketServer.BaseRequestHandler):
    def handle(self):
        data = self.request[0].strip()
        dns = SinDNSFrame(data)
        socket = self.request[1]
        if(dns.query.type==1):
            name = dns.getname();
            toip = None
            ifrom = "map"
            if (int(rs.exists(name)) == 1):
                toip = str(rs.get(name))
            else:
                try:
                    qdns = query_DNS
                    reip = qdns.domain_to_ip('8.8.8.8','www.baidu.com')
                    toip = reip[0] if 0 < len(reip) else None
                    ifrom = "sev"
                    sev.redisaddname(name, toip)
                except Exception, e:
                    print '--------------------------------'
                    print 'get ip fail'
                    print repr(e)
                    print 'client_address,hostname,toip'
                    print self.client_address
                    print name
                    print toip
                    print '--------------------------------'
            if toip:
                dns.setip(toip)
            print '%s: %s-->%s (%s)'%(self.client_address[0], name, toip, ifrom)
            socket.sendto(dns.getbytes(), self.client_address)
        else:
            socket.sendto(data, self.client_address)

class SinDNSServer:
    def __init__(self,host='0.0.0.0',port=53):
        #set Host,Port
        self.port = port
        self.host = host
    def redisaddname(self, name, ip):
        outTime = '600' #second
        rs.set(name,ip)
        rs.expire(name,outTime)
    def start(self):
        print 'host: '+self.host+' , port: '+str(self.port)
        HOST, PORT = self.host, self.port
        server = SocketServer.UDPServer((HOST, PORT), SinDNSUDPHandler)
        print 'server starting'
        server.serve_forever()

if __name__ == "__main__":
    #redis conf
    redis_host = 'localhost'
    redis_port = '6379'
    redis_db = '1'
    rs = redis.StrictRedis(host=redis_host,port=redis_port,db=redis_db)
    sev = SinDNSServer()
    #test Redis
    try:
        sev.redisaddname('dlocalhost', '127.0.0.1')
    except Exception, e:
        print 'Redis Set ERROR!'
        print repr(e)
        exit(1)
    #start Servrt
    sev.start()
