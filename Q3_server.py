import socket
import time
import argparse
# I first imported the necessary libraries and defined the host and port
host = "127.0.0.1"
port = 12345
# this is for parsing the command line arguments to disable/enable Nagle's algorithm and Delayed ACK
parser = argparse.ArgumentParser(description="TCP Server with Nagle and Delayed ACK control.")
parser.add_argument("--nagle", action="store_true", help="enable Nagle's algorithm")
parser.add_argument("--delayed_ack", action="store_true", help="enable Delayed ACK")
parser.add_argument("--config_name", default="Server Test", help="Name of the configuration")
args = parser.parse_args()

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # I then created a server socket and bound it to the host and port
server_socket.bind((host, port)) 
server_socket.listen(1) # I then started listening for incoming connections

try:
    conn, addr = server_socket.accept() # I then accepted the incoming connection
    results = {
        'throughput': 0,
        'goodput': 0,
        'packet_loss_rate': 0,
        'max_packet_size_received': 0,
        'packets_received': 0,
        'packet_loss_count': 0,
        'received_times': []
    } # I then defined the results dictionary to store the results


    nagle_enabled = args.nagle # I then set the Nagle's algorithm and Delayed ACK based on the command line arguments
    delayed_ack_enabled = args.delayed_ack
    total_bytes_received = 0 # I then initialized the variables to store the results
    packets_received = 0
    packet_sizes_received = []
    packet_loss_count = 0
    received_times = []
    start_time = time.time()

    try:
        # I then set up the server socket to disable Nagle's algorithm and Delayed ACK same as client
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 0)
        conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 0)
        if not nagle_enabled:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        if not delayed_ack_enabled:
            conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
        while True:
            data = conn.recv(1024) # I then received the data from the client
            if not data:
                break
            total_bytes_received += len(data) # I then incremented the number of bytes received
            packets_received += 1 # and the number of packets received
            packet_sizes_received.append(len(data)) # I then stored the packet size received
            received_times.append(time.time()) # and the time the packet was received

    except ConnectionResetError:
        packet_loss_count += 1 # If there is a connection reset error, I increment the packet loss count
    except Exception as e:
        print(f"Server error: {e}")
    finally:
        conn.close()

    end_time = time.time()
    elapsed_time = end_time - start_time # I then calculated the elapsed time
    throughput = total_bytes_received / elapsed_time if elapsed_time > 0 else 0
    goodput = throughput  # I am assuming no application layer overhead as the data is sent as is in byte form
    max_packet_size_received = max(packet_sizes_received) if packet_sizes_received else 0 # I then calculated the maximum packet size received
    # I then stored the results in the results dictionary
    results['throughput'] = throughput
    results['goodput'] = goodput
    results['packet_loss_rate'] = packet_loss_count
    results['max_packet_size_received'] = max_packet_size_received
    results['packets_received'] = packets_received
    results['packet_loss_count'] = packet_loss_count
    results['received_times'] = received_times

except Exception as e:
    print(f"Server error: {e}")
finally:
    server_socket.close()

# I then printed the results
print(f"Results for {args.config_name}:")
print(f"  Throughput: {results['throughput']:.2f} bytes/second")
print(f"  Goodput: {results['goodput']:.2f} bytes/second")
print(f"  Packet loss rate: {results['packet_loss_rate']:.4f}")
print(f"  Max packet size received: {results['max_packet_size_received']} bytes")
print(f"  Packets received: {results['packets_received']}")
print(f"  Packet loss count: {results['packet_loss_count']}")
print("-" * 30)

# References
# https://en.wikipedia.org/wiki/Nagle%27s_algorithm#Disabling_either_Nagle_or_delayed_ACK
# https://en.wikipedia.org/wiki/Nagle%27s_algorithm#Operating_systems_implementation
# https://stackoverflow.com/questions/31826762/python-socket-send-immediately