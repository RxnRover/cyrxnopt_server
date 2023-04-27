import zmq


def init_socket(address: str) -> zmq.Socket:
    """Initialize a ZMQ socket.

    :param address: IP address to bind the socket to.
    :type address: str

    :return: Initialized ZMQ socket.
    :rtype: zmq.Socket
    """

    print("Binding socket at {} ...".format(address))

    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect(address)

    print("Binding complete!")

    return socket
