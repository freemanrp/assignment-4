import socket
import sys
import os
import base64


def download_file_data(client_socket, server_addr, data_port, filename, size):
    try:
        with open(filename, 'wb') as fos:
            start = 0
            while start < size:
                request = f'FILE {filename} GET START {start} END {start + 999}'
                client_socket.sendto(request.encode(), (server_addr, data_port))
                client_socket.settimeout(5)
                try:
                    recv_data, _ = client_socket.recvfrom(65535)
                    response = recv_data.decode().strip()
                    parts = response.split()
                    if len(parts) >= 6 and parts[0] == 'FILE' and parts[1] == filename and parts[2] == 'OK':
                        current_start = int(parts[3])
                        end = int(parts[5])
                        data_segment = parts[6]
                        decoded_data = base64.b64decode(data_segment)
                        fos.write(decoded_data)
                        start = end + 1
                except socket.timeout:
                    print(f'Timeout waiting for FILE OK response for {filename}')
                    break
        close_request = f'FILE {filename} CLOSE'
        client_socket.sendto(close_request.encode(), (server_addr, data_port))
        client_socket.settimeout(5)
        try:
            recv_data, _ = client_socket.recvfrom(1024)
            response = recv_data.decode().strip()
            if response.startswith(f'FILE {filename} CLOSE_OK'):
                print(f'Successfully downloaded {filename}')
        except socket.timeout:
            print(f'Timeout waiting for CLOSE_OK response for {filename}')
    except Exception as e:
        print(f'Error downloading {filename}: {e}')
def download_file(client_socket, hostname, port, filename):
    try:
        server_addr = hostname
        request = f'DOWNLOAD {filename}'
        client_socket.sendto(request.encode(), (server_addr, port))
        client_socket.settimeout(5)
        try:
            recv_data, _ = client_socket.recvfrom(1024)
            response = recv_data.decode().strip()
            parts = response.split()
            if len(parts) >= 4 and parts[0] == 'OK':
                file = parts[1]
                size = int(parts[3])
                data_port = int(parts[5])
                download_file_data(client_socket, server_addr, data_port, file, size)
            elif len(parts) >= 3 and parts[0] == 'ERR':
                print(f'File not found: {filename}')
        except socket.timeout:
            print(f'Timeout waiting for download response for {filename}')
    except Exception as e:
        print(f'Error downloading {filename}: {e}')
def main():
    if len(sys.argv) != 4:
        print("Usage: python3 UDPClient.py <hostname> <port> <files.txt>")
        return
    hostname = sys.argv[1]
    port = int(sys.argv[2])
    files_txt = sys.argv[3]
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        with open(files_txt, 'r') as br:
            for line in br:
                filename = line.strip()
                if filename:
                    download_file(client_socket, hostname, port, filename)
    except Exception as e:
        print(f'Error reading files.txt: {e}')
    finally:
        client_socket.close()

if __name__ == '__main__':
    main()