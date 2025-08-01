#!/usr/bin/env python

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


def topology(args):
    "Create a network."
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    sta1 = net.addStation('sta1', position='15,20,0', mac='00:00:00:00:10:01', ip='10.0.0.2/8', bgscan_threshold=-30, s_inverval=2, l_interval=10, bgscan_module="simple")
    UDPS = net.addStation('UDPS', mac='00:00:00:00:10:02', ip='10.0.0.5/8', position='60,35,0')
    ap1 = net.addAccessPoint('ap1', mac='00:00:00:00:10:03', ssid="handover",
                             mode="g", channel="1", passwd='123456789a',
                             encrypt='wpa2', position='10,30,0', datapath='user')
    ap2 = net.addAccessPoint('ap2', mac='00:00:00:00:10:04', ssid="handover",
                             mode="g", channel="6", passwd='123456789a',
                             encrypt='wpa2', position='60,30,0', datapath='user')
    c1 = net.addController('c1')

    info("*** Configuring Propagation Model\n")
    net.setPropagationModel(model="logDistance", exp=3.5)

    info("*** Configuring nodes\n")
    net.configureNodes()

    info("*** Creating links\n")
    net.addLink(ap1, ap2)
    
    if '-p' not in args:
        net.plotGraph(min_x=-100, min_y=-100, max_x=200, max_y=200)
	
    info("*** Bringing up hwsim0 interface\n")
    os.system('ifconfig hwsim0 up')
    info("*** Starting packet capture on hwsim0\n")
    os.system('tcpdump -i hwsim0 -w sim11.pcap &')
    net.startMobility(time=0)
    net.mobility(sta1, 'start', time=1, position='15,20,0')
    net.mobility(sta1, 'stop', time=25, position='65,20,0')
    net.stopMobility(time=27)
    
    info("*** Starting network\n")
    net.build()
    c1.start()
    ap1.start([c1])
    ap2.start([c1])
    makeTerm(UDPS, cmd="bash -c 'iperf3 -s -p 5566 --logfile sim11;'")
    time.sleep(5)
    makeTerm(sta1, cmd="bash -c 'iperf3 -c 10.0.0.5 -u -t 25 -b 3m -p 5566;'")
    info("*** Running CLI\n")
    CLI(net)

    info("*** Stopping network\n")
    net.stop()


if __name__ == '__main__':
    setLogLevel('info')
    topology(sys.argv)
