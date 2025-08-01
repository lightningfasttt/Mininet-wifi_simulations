#!/usr/bin/python

import sys
from mininet.node import Controller
from mininet.log import setLogLevel, info
from mn_wifi.cli import CLI
from mn_wifi.net import Mininet_wifi
from mininet.term import makeTerm
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
import time
import os

def topology():
    "Create a network."
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)
    
    info("*** Creating nodes\n")
    # Stations and access point
    sta1 = net.addStation('sta1', mac='00:00:00:00:00:01', ip='10.0.0.1/8', position='30,70,0')
    sta2 = net.addStation('sta2', mac='00:00:00:00:00:02', ip='10.0.0.2/8', position='50,70,0')
    sta3 = net.addStation('sta3', mac='00:00:00:00:00:03', ip='10.0.0.3/8', position='70,70,0')
    ap1 = net.addAccessPoint('ap1', mac='00:00:00:00:10:02', ssid='handover', mode='g', channel='1', position='50,65,0')
    c1 = net.addController('c1')
    
    net.setPropagationModel(model="logDistance", exp=5)
    
    info("*** Configuring wifi nodes\n")
    net.configureWifiNodes()    

    info("*** Bringing up hwsim0 interface\n")
    os.system('ifconfig hwsim0 up')
    
    info("*** Starting packet capture on hwsim0\n")
    os.system('tcpdump -i hwsim0 -w sim15.pcap &')
    
    net.plotGraph(min_x=-20, min_y=-10, nax_x=150, max_y=150)
    info("*** Starting network\n")
    net.build()
    c1.start()
    ap1.start([c1])

    # Start iperf servers on UDPS
    makeTerm(sta2, cmd="bash -c 'iperf -s -u -p 5565;'")
    makeTerm(sta2, cmd="bash -c 'iperf -s -u -p 5566;'")
    
    time.sleep(5)

    # Start iperf clients on sta1 and sta3
    makeTerm(sta1, cmd="bash -c 'iperf -c 10.0.0.2 -u -t 15 -b 100m -p 5565;'")
    makeTerm(sta3, cmd="bash -c 'iperf -c 10.0.0.2 -u -t 15 -b 100m -p 5566;'")

    info("*** Running CLI\n")
    CLI(net)
    
    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()

