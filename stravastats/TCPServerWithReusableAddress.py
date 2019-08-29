import socketserver

class TCPServerWithReusableAddress(socketserver.TCPServer):
    # Allow the server to reuse an address. The default of False 
    # means that stopping and then restarting the server in quick 
    # succession leads to an error
    allow_reuse_address = True

    # TODO: Is there a more elegant way of doing this?
    def __init__(self, host_port_tuple, stream_handler, client, secret_keys):
        super().__init__(host_port_tuple, stream_handler)
        self.client = client
        self.secret_keys = secret_keys
