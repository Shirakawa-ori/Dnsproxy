# Dnsproxy_redis

Python2

需要用到Redis

pip install redis

如果出现端口占用错误：socket.error: [Errno 98] Address already in use

检查dnsmasq是否在运行

测试：
yum install bind-utils

dig @127.0.0.1 www.baidu.com
