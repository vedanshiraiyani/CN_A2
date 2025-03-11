import socket # I first imported the required libraries
import time
import argparse

host = "127.0.0.1" # I defined the host and port
port = 12345
data_size = 4 * 1000 # I defined the data size, transfer rate and duration. I will be changing these to get different results
transfer_rate = 40
duration = 120

# I then parse the command line arguments to disable/enable Nagle's algorithm and Delayed ACK 
parser = argparse.ArgumentParser(description="TCP Client with Nagle and Delayed ACK control.")
parser.add_argument("--nagle", action="store_true", help="enable Nagle's algorithm")
parser.add_argument("--delayed_ack", action="store_true", help="enable Delayed ACK")
parser.add_argument("--config_name", default="Client Test", help="Name of the configuration")
args = parser.parse_args()

results = {
    'packets_sent': 0,
    'packet_loss_count': 0,
    'max_packet_size_sent': 0,
    'sent_times': []
} # I defined the results dictionary to store the results

nagle_enabled = args.nagle # I then set the Nagle's algorithm and Delayed ACK based on the command line arguments
delayed_ack_enabled = args.delayed_ack

total_bytes_sent = 0 # I then initialized the variables to store the results
packets_sent = 0
packet_sizes_sent = []
packet_loss_count = 0
sent_times = []
start_time = time.time()

try: # I then created a client socket and connected to the server
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 0)
    client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 0)
    if not nagle_enabled: # If the Nagle's algorithm is disabled, I set the TCP_NODELAY option
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    if not delayed_ack_enabled: # If the Delayed ACK is disabled, I set the TCP_QUICKACK option
        client_socket.setsockopt(socket.IPPROTO_TCP, socket.TCP_QUICKACK, 1)
    client_socket.connect((host, port))  # I then connected to the server

    sent_data = b'A' * data_size # I then created the data to be sent
    sent_index = 0  # I then initialized the variables to store the number of bytes sent
    while time.time() - start_time < duration and sent_index < data_size:
        send_chunk_size = min(transfer_rate, data_size - sent_index) # I then sent the data in chunks
        chunk = sent_data[sent_index:sent_index + send_chunk_size] # I then sent the data in chunks
        client_socket.sendall(chunk) # I then sent the data in chunks
        total_bytes_sent += len(chunk) # I then incremented the number of bytes sent
        packets_sent += 1 # and the number of packets sent
        packet_sizes_sent.append(len(chunk)) # I then stored the packet size sent
        sent_times.append(time.time()) # and the time the packet was sent
        sent_index += send_chunk_size # I then incremented the index
        time.sleep(1)  # enforce the transfer rate.
    client_socket.close() # I then closed the client socket

except ConnectionResetError:
    packet_loss_count += 1 # If there is a connection reset error, I increment the packet loss count
except Exception as e:
    print(f"Client error: {e}") # If there is any other error, I print the error message

end_time = time.time()
elapsed_time = end_time - start_time # I then calculated the elapsed time

results['packets_sent'] = packets_sent
results['packet_loss_count'] = packet_loss_count
results['max_packet_size_sent'] = max(packet_sizes_sent) if packet_sizes_sent else 0
results['sent_times'] = sent_times


# I then printed the results
print(f"Results for {args.config_name}:")
print(f"  Max packet size sent: {results['max_packet_size_sent']} bytes")
print(f"  Packets sent: {results['packets_sent']}")
print(f"  Packet loss count: {results['packet_loss_count']}")
print("-" * 30)
