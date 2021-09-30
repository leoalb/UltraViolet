#!/usr/bin/env python3
"""
Testing Fog-Edge Network Topology - 6 Hosts with variable bandwidth
Fog1 and Fog2 have two NIC each for different network
"""

import time

from MaxiNet.Frontend import maxinet
from MaxiNet.Frontend.container import Docker
from mininet.topo import Topo
from mininet.node import OVSSwitch

# Creating Topology
topo = Topo()
f1 = topo.addHost("f1", ip="10.0.0.10", cls=Docker, dimage="ubuntu:trusty")
f2 = topo.addHost("f2", ip="10.0.0.11", cls=Docker, dimage="ubuntu:trusty")
e1 = topo.addHost("e1", ip="10.0.1.12", cls=Docker, dimage="ubuntu:trusty")
e2 = topo.addHost("e2", ip="10.0.1.13", cls=Docker, dimage="ubuntu:trusty")
e3 = topo.addHost("e3", ip="10.0.1.14", cls=Docker, dimage="ubuntu:trusty")
e4 = topo.addHost("e4", ip="10.0.1.13", cls=Docker, dimage="ubuntu:trusty")

s1 = topo.addSwitch("s1")
s2 = topo.addSwitch("s2")
s3 = topo.addSwitch("s3")

topo.addLink(f1, s1, bw = 125, delay="50ms")
topo.addLink(f2, s1, bw = 125, delay="50ms")
topo.addLink(f1, s2, intfName1="f1-eth1", params1={'ip':'10.0.2/8'})
topo.addLink(f2, s3, intfName1="f2-eth1", params1={'ip':'10.0.2/8'})
topo.addLink(e1, s2, bw = 25, delay="200ms")
topo.addLink(e2, s2, bw = 25, delay="200ms")
topo.addLink(e3, s3, bw = 10, delay="20ms")
topo.addLink(e4, s3, bw = 10, delay="20ms")

#topo.addLink(f1, s2, intfName1="f1-eth1", params1={'ip':'10.0.1/8'})
#topo.addLink(f2, s3, intfName1="f2-eth1", params1={'ip':'10.0.2/8'})


cluster = maxinet.Cluster()
exp = maxinet.Experiment(cluster, topo, switch=OVSSwitch)
exp.setup()

try:

    print("Waiting 3 secs to converge")
    time.sleep(3)

    print(exp.get_node("f1").cmd("ifconfig"))
    print(exp.get_node("f2").cmd("ifconfig"))
    print(exp.get_node("f1").cmd("ifconfig f1-eth0 10.0.0.10 netmask 255.255.255.0"))
    print(exp.get_node("f2").cmd("ifconfig f2-eth0 10.0.0.11 netmask 255.255.255.0"))
  #  print("f1 -> f2")
  #  print(exp.get_node("f1").cmd("ping -I f1-eth0 -c 3 10.0.0.11"))
  #  print("f2 -> f1")
  #  print(exp.get_node("f2").cmd("ping -c 3 10.0.0.10"))
  #  print("e1 -> f1")
  #  print(exp.get_node("e1").cmd("ping -c 3 10.0.2.0"))
  #  print("e2 -> e1")
  #  print(exp.get_node("e2").cmd("ping -c 3 10.0.1.12"))
  #  print("e3 -> f1")
  #  print(exp.get_node("e3").cmd("ping -c 3 10.0.0.10"))
  #  print("e4 -> f2")
  #  print(exp.get_node("e4").cmd("ping -c 3 10.0.2.0"))


    node_f1 = exp.get_node("f1")

    print("Testing methods:")
    print("updateCpuLimit():")
   # print("\t" + str(node_f1.updateCpuLimit(10000, 10000, 1, "0-1")))  # cpu_quota, cpu_period, cpu_shares, cores
    # cpu_quota, cpu_period, cpu_shares, cores
    print("\t" + str(node_f1.updateCpuLimit(10000, 10000, 1, "0")))

    print("updateMemoryLimit():")
    print("\t" + str(node_f1.updateMemoryLimit(300000)))

    print("cgroupGet():")
    print("\t" + str(node_f1.cgroupGet('cpus', resource='cpuset')))

    print("")
    print("Testing attributes:")
    print("dimage = " + str(node_f1.dimage))
    print("resources = " + str(node_f1.resources))
    print("volumes = " + str(node_f1.volumes))

    exp.CLI(locals(), globals())


finally:
    exp.stop()
