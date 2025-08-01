from mn_wifi.net import Mininet_wifi
from mininet.node import Controller
from mn_wifi.cli import CLI
from mn_wifi.link import wmediumd
from mn_wifi.wmediumdConnector import interference
from mininet.log import setLogLevel, info
import os
import time
import threading
import re

def topology():
    net = Mininet_wifi(controller=Controller, link=wmediumd, wmediumd_mode=interference)

    info("*** Creating nodes\n")
    # Create stations and access point
    sta1 = net.addStation('sta1', position='0,5,0')  # PSM-enabled station
    sta2 = net.addStation('sta2', position='15,10,0')
    sta3 = net.addStation('sta3', position='20,10,0')
    sta4 = net.addStation('sta4', position='15,20,0')
    #sta5 = net.addStation('sta5', position='25,10,0')  # Traffic generator station
    ap1 = net.addAccessPoint('ap1', ssid='simplewifi', mode='g', channel='1', position='15,15,0')
    c1 = net.addController('c1')
    
    # Set propagation model with a realistic path loss exponent
    net.setPropagationModel(model="logDistance", exp=5)  # Adjusted exponent to 

    info("*** Configuring Wi-Fi nodes\n")
    net.configureWifiNodes()

    # Plot the graph
    info("*** Plotting network graph\n")
    net.plotGraph(min_x=-70, min_y=-60, nax_x=80, max_y=80)  # Adjust max_x and max_y as needed

    info("*** Bringing up hwsim0 interface\n")
    os.system('ifconfig hwsim0 up')

    info("*** Starting packet capture on hwsim0\n")
    os.system('tcpdump -i hwsim0 -w sim11.pcap &')

    info("*** Starting network\n")
    net.build()
    c1.start()
    ap1.start([c1])
    
    info("*** Assigning IP addresses\n")
    # Assign IP addresses to the stations
    sta1.setIP('10.0.0.1/24')
    sta2.setIP('10.0.0.2/24')
    sta3.setIP('10.0.0.3/24')
    sta4.setIP('10.0.0.4/24')
    #sta5.setIP('10.0.0.5/24')

    info("*** Enabling Power Saving Mode on STA1\n")
    # Enable PSM on STA1
    sta1.cmd('iw dev %s set power_save on' % sta1.params['wlan'][0])

    # Wait for stations to associate
    info("*** Waiting for stations to associate\n")
    time.sleep(10)

    info("*** Testing network connectivity\n")
    net.pingAll()

    info("*** Measuring initial packet counts\n")
    def background_traffic(src, dst):
    	print(f"Starting iperf server on {dst.name}")
    	dst.cmd('iperf -u -s -p 5002 &')
    	time.sleep(2)  # Wait for server to start
    	print(f"Starting iperf client on {src.name} connecting to {dst.name}")
    	src.cmd('iperf -u -c %s -t 60 -b 5m -p 5002 &' % dst.IP())
    	
    # Start background traffic
    #background_traffic(sta4, sta5)

    def get_packet_counts(station):
        iface = station.params['wlan'][0]
        print(f"Station {station.name} interface: {iface}")

        # Check if interface exists
        iface_check = station.cmd(f'ls /sys/class/net/{iface}')
        if 'No such file' in iface_check:
            print(f"Interface {iface} does not exist for {station.name}.")
            return 0, 0

        # Check interface state
        iface_state = station.cmd(f'cat /sys/class/net/{iface}/operstate').strip()
        if iface_state != 'up':
            print(f"Interface {iface} is not up for {station.name}. Current state: {iface_state}")

        # Read packet counts
        tx_cmd = f'cat /sys/class/net/{iface}/statistics/tx_packets'
        rx_cmd = f'cat /sys/class/net/{iface}/statistics/rx_packets'
        tx_output = station.cmd(tx_cmd)
        rx_output = station.cmd(rx_cmd)
        print(f"Station {station.name} TX command output: '{tx_output.strip()}'")
        print(f"Station {station.name} RX command output: '{rx_output.strip()}'")

        # Extract numeric values
        tx_match = re.search(r'(\d+)', tx_output)
        rx_match = re.search(r'(\d+)', rx_output)
        if tx_match and rx_match:
            tx_packets = int(tx_match.group(1))
            rx_packets = int(rx_match.group(1))
        else:
            print(f"Could not parse packet counts for {station.name}. TX output: '{tx_output}', RX output: '{rx_output}'")
            tx_packets = 0
            rx_packets = 0
        return tx_packets, rx_packets

    # Initial packet counts
    tx_sta1_start, rx_sta1_start = get_packet_counts(sta1)
    tx_sta2_start, rx_sta2_start = get_packet_counts(sta2)
    tx_sta3_start, rx_sta3_start = get_packet_counts(sta3)

    info("*** Generating UDP CBR traffic from sta4 to other stations\n")
    # Start iperf servers on stations
    for sta in [sta1, sta2, sta3]:
        sta.cmd('iperf -u -s -p 5001 >/dev/null 2>&1 &')

    # Allow the servers some time to start
    time.sleep(8)

    # On sta4, generate UDP CBR traffic to all stations
    data_rate = "10m"
    duration = 25       # 25 seconds
    udp_payload_size = 1024  # 1024 bytes

    for dst_sta in [sta1, sta2, sta3]:
        info(f"*** sta4 generating UDP traffic to {dst_sta.name}\n")
        sta4.cmd(f'iperf -u -c {dst_sta.IP()} -t {duration} -b {data_rate} -p 5001 -l {udp_payload_size} >/dev/null 2>&1 &')

    # Wait for traffic generation to complete
    time.sleep(duration + 5)  # Adjust based on traffic duration

    # Final packet counts
    tx_sta1_end, rx_sta1_end = get_packet_counts(sta1)
    tx_sta2_end, rx_sta2_end = get_packet_counts(sta2)
    tx_sta3_end, rx_sta3_end = get_packet_counts(sta3)

    # Calculate the difference
    tx_sta1 = tx_sta1_end - tx_sta1_start
    rx_sta1 = rx_sta1_end - rx_sta1_start
    tx_sta2 = tx_sta2_end - tx_sta2_start
    rx_sta2 = rx_sta2_end - rx_sta2_start
    tx_sta3 = tx_sta3_end - tx_sta3_start
    rx_sta3 = rx_sta3_end - rx_sta3_start

    info("*** Power Consumption (approximated by packet counts)\n")
    info(f"STA1 (PSM Enabled): TX={tx_sta1}, RX={rx_sta1}\n")
    info(f"STA2: TX={tx_sta2}, RX={rx_sta2}\n")
    info(f"STA3: TX={tx_sta3}, RX={rx_sta3}\n")

    # Measure latency from each station to sta4
    # Start the CLI
    info("*** Running CLI\n")
    CLI(net)

    # Stop tcpdump
    info("*** Stopping packet capture\n")
    os.system('pkill tcpdump')

    info("*** Stopping network\n")
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    topology()

