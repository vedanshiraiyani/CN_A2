from mininet.net import Mininet
from mininet.topo import Topo
from mininet.node import OVSController
import subprocess
import time
import os

def setup_topology(option, link_loss=None):
    class CustomTopo(Topo):
        def build(self):
            s1 = self.addSwitch('s1')
            s2 = self.addSwitch('s2')
            s3 = self.addSwitch('s3')
            s4 = self.addSwitch('s4')

            h1 = self.addHost('h1')
            h2 = self.addHost('h2')
            h3 = self.addHost('h3')
            h4 = self.addHost('h4')
            h5 = self.addHost('h5')
            h6 = self.addHost('h6')
            h7 = self.addHost('h7')

            self.addLink(h1, s1)
            self.addLink(h2, s1)
            self.addLink(h3, s2)
            self.addLink(h4, s2)
            self.addLink(h5, s3)
            self.addLink(h6, s3)
            self.addLink(h7, s4)

            self.addLink(s1, s2)
            self.addLink(s2, s3)
            self.addLink(s3, s4)

    net = Mininet(topo=CustomTopo(), controller=OVSController)
    net.start()

    for switch in ['s1', 's2', 's3', 's4']:
        net.get(switch).cmd('ovs-ofctl add-flow %s actions=normal' % switch)

    if option in ['c','d']:
        net.get('s1').cmd('tc qdisc add dev s1-eth1 root tbf rate 100Mbit burst 10kb latency 50ms')
        net.get('s2').cmd('tc qdisc add dev s2-eth2 root tbf rate 50Mbit burst 5kb latency 50ms')
        net.get('s3').cmd('tc qdisc add dev s3-eth3 root tbf rate 100Mbit burst 10kb latency 50ms')
        
        if option == 'd' and link_loss is not None:
            net.get('s2').cmd(f'tc qdisc add dev s2-eth2 root netem loss {link_loss}%')
    
    return net

def analyze_pcap():
    if not os.path.exists("iperf_capture.pcap") or os.path.getsize("iperf_capture.pcap") == 0:
        print("[ERROR] No packets were captured. Check tcpdump settings!")
        return

    throughput = subprocess.getoutput("tshark -r iperf_capture.pcap -q -z io,stat,10 | grep '<>'")
    goodput = int(subprocess.getoutput("tshark -r iperf_capture.pcap -Y 'tcp.len > 0' | wc -l").strip().split('\n')[-1])

    # Count lost packets
    lost_packets = int(subprocess.getoutput("tshark -r iperf_capture.pcap -Y 'tcp.analysis.lost_segment' 2>/dev/null | wc -l").strip().split('\n')[-1])


    # Count total TCP packets sent
    total_packets = int(subprocess.getoutput("tshark -r iperf_capture.pcap -Y 'tcp' 2>/dev/null | wc -l").strip().split('\n')[-1])
    goodput = goodput/total_packets * 100
    

    # Calculate packet loss rate
    if total_packets > 0:
        packet_loss_rate = (lost_packets / total_packets) * 100
    else:
        packet_loss_rate = 0

    max_packet_size = subprocess.getoutput("tshark -r iperf_capture.pcap -T fields -e frame.len | sort -nr | head -1")
    
    print("Throughput:", throughput)
    print("Goodput (total data packets received):", goodput)
    print(f"Packet loss rate: {packet_loss_rate:.2f}%")
    print("Maximum packet size achieved:", max_packet_size)


def run_iperf_test(net, option, cc_scheme, condition=None, link_loss=None):
    server = net.get('h7')
    server.cmd('tcpdump -i h7-eth0 port 5001 -w iperf_capture.pcap &')
    server.cmd('iperf3 -s -p 5001 &')
    time.sleep(2)
    
    clients = {
        'a': [('h1', 0, 150)],
        'b': [('h1', 0, 150), ('h3', 15, 120), ('h4', 30, 90)],
        'c': {  # Map conditions to client-server setups
            'a': [('h1', 0, 150)],
            'b': [('h1', 0, 150), ('h3', 15, 120), ('h4', 30, 120)],
            'c': [('h1', 0, 150), ('h3', 15, 120), ('h4', 30, 120)]
        },
        'd': {  # Loss configurations
            'a': [('h1', 0, 150)],
            'b': [('h1', 0, 150), ('h3', 15, 120), ('h4', 30, 120)],
            'c': [('h1', 0, 150), ('h3', 15, 120), ('h4', 30, 120)]
        }
    }
    
    test_clients = clients[option] if option in ['a', 'b'] else clients[option][condition]
    
    for host, delay, duration in test_clients:
        time.sleep(delay)
        client = net.get(host)
        client.cmd(f'iperf3 -c 10.0.0.7 -p 5001 -b 10M -P 10 -t {duration} -C {cc_scheme} > {host}_{cc_scheme}.txt &')
    
    time.sleep(160)
    server.cmd('pkill tcpdump')
    analyze_pcap()
    print("Tests completed! Results saved to iperf_capture.pcap and *_{cc_scheme}.txt")

def cleanup():
    os.system('sudo pkill iperf3')
    os.system('sudo mn -c')

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 3:
        print("Usage: python3 script.py <option> <congestion_control_scheme>")
        sys.exit(1)
    
    option = sys.argv[1]
    cc_scheme = sys.argv[2]
    
    if option not in ['a', 'b', 'c', 'd']:
        print("Invalid option! Choose from a, b, c, or d.")
        sys.exit(1)
    
    condition = None
    link_loss = None
    
    if option in ['c','d']:
        condition = input("Select condition (a, b, c): ")
        if condition not in ['a', 'b', 'c']:
            print("Invalid condition!")
            sys.exit(1)
    
    if option == 'd':
        link_loss = int(input("Select link loss percentage (1% or 5%): "))
        if link_loss not in [1, 5]:
            print("Invalid loss percentage!")
            sys.exit(1)
    
    cleanup()
    net = setup_topology(option, link_loss)
    run_iperf_test(net, option, cc_scheme, condition, link_loss)
    net.stop()
    cleanup() 