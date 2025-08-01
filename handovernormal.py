#!/us/bin/python

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
	sta1 = net.addStation('sta1', mac='00:00:00:00:00:02', ip='10.0.0.2/8', position='10,40,0')
	UDPS = net.addStation('UDPS', mac='00:00:00:00:00:04', ip='10.0.0.5/8', position='60,20,0')
	ap1 = net.addAccessPoint('ap1', mac='00:00:00:00:10:02', ssid='handover', mode='g', channel='1', position='15,30,0')
	ap2 = net.addAccessPoint('ap2', mac='00:00:00:00:10:03', ssid='handover', mode='g', channel='6', position='55,30,0')
	c1 = net.addController('c1')
	
	net.setPropagationModel(model="logDistance", exp=5)
	
	info("*** Configuring wifi nodes\n")
	net.configureWifiNodes()
	
	info("*** Creating Links\n")
	net.addLink(ap1, ap2)
	
	net.plotGraph(min_x=-20, min_y=-10, nax_x=90, max_y=70)
	
	info("*** Bringing up hwsim0 interface\n")
	os.system('ifconfig hwsim0 up')
	
	info("*** Starting packet capture on hwsim0\n")
	os.system('tcpdump -i hwsim0 -w sim11.pcap &')
	 
	net.startMobility(time=0)
	net.mobility(sta1, 'start', time=2, position='10,40,0')
	net.mobility(sta1, 'stop', time=25, position='60,40,0')
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
	topology()
