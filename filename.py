from socket import *
import socket
import os
def name(file):
    str=""
    for c in file:
        if c == '/':
            str=""
        else:
            str+=c
    return str
def name2(file):
    str=""
    for c in file:
        if c == '\\':
            str=""
        else:
            str+=c
    return str
def start_client(socket_filename,number):
    host = "192.168.137.122"  # 服务端主机地址
    port = 8080  # 服务端端口号

    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client_socket.connect((host, port))

    # 发送数字

    client_socket.sendall(str(number).encode())

    # 发送文件
    filepath = socket_filename
    try:
        with open(filepath, "rb") as file:
            # 发送文件名长度和文件名
            filename = file.name.split("/")[-1]
            filename_length = len(filename)
            client_socket.sendall(str(filename_length).encode())
            client_socket.sendall(filename.encode())

            # 发送文件大小
            file_size = os.path.getsize(filepath)
            client_socket.sendall(file_size.to_bytes(4, byteorder='big'))

            # 发送文件内容
            filedata = file.read()
            client_socket.sendall(filedata)

            print(f"文件:{filename}发送成功！")

        # 接收处理后的文件
        filename_length = int(client_socket.recv(2).decode())
        filename = client_socket.recv(filename_length).decode()


        # 接收文件大小
        file_size_bytes = client_socket.recv(4)
        file_size = int.from_bytes(file_size_bytes, byteorder='big', signed=False)


        # 指定保存文件的目录
        save_dir = "mha"
        os.makedirs(save_dir, exist_ok=True)

        # 拼接文件路径
        save_path = os.path.join(save_dir, filename)

        # 接收文件内容
        received_bytes = 0
        with open(save_path, "wb") as file:
            while received_bytes < file_size:
                data = client_socket.recv(1024)
                if not data:
                    break
                file.write(data)
                received_bytes += len(data)
        save_path = "mha/" + name2(save_path)
        print(f"文件内容已保存到：{save_path}")
        return save_path

    except FileNotFoundError:
        print(f"没有找到文件: {filepath}")

    client_socket.close()
def kon(pixmap):
    return pixmap

