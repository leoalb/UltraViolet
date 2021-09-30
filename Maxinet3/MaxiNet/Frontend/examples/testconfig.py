#!/usr/bin/env python3
"""
Testing Network Topology - 3 Hosts with variable bandwidth
"""

import time

from MaxiNet.Frontend import maxinet
from mininet.topo import Topo
from mininet.node import OVSSwitch

topo = Topo()
d1 = topo.addHost("d1", ip="10.0.0.10")
d2 = topo.addHost("d2", ip="10.0.0.11")
d3 = topo.addHost("d3", ip="10.0.0.12")

s1 = topo.addSwitch("s1")
topo.addLink(d1, s1, bw = 9, loss=2)
topo.addLink(d2, s1, bw = 2)
topo.addLink(d3, s1, bw = 5, delay="1ms")

cluster = maxinet.Cluster()
exp = maxinet.Experiment(cluster, topo, switch=OVSSwitch)
exp.setup()

try:
   # print(exp.get_node("d1").cmd("ifconfig"))
   # print(exp.get_node("d2").cmd("ifconfig"))

    print("Waiting 3 secs to converge")
    time.sleep(3)

    print(exp.get_node("d1").cmd("ping -c 5 10.0.0.11"))
    print(exp.get_node("d2").cmd("ping -c 5 10.0.0.12"))
    print(exp.get_node("d3").cmd("ping -c 5 10.0.0.10"))

finally:
    exp.stop()
