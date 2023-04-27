import json
import random

# import numpy as np
import zmq
from benchmarking.functions.branin import branin
from benchmarking.functions.goldstein_price import goldstein_price
from benchmarking.functions.hartmann import hartmann
from benchmarking.functions.rosenbrock import rosenbrock
from benchmarking.functions.shekel import shekel
from benchmarking.functions.shubert import shubert
from benchmarking.functions.six_hump_camel import six_hump_camel


# TODO: Move this into a unit test, probably
def main():
    # REQUEST_TIMEOUT = 2500  # ms
    # REQUEST_RETRIES = 1
    SERVER_ENDPOINT = "tcp://*:5555"

    # Create the context and socket
    context = zmq.Context(1)
    socket = context.socket(zmq.REP)

    print("Binding to {}".format(SERVER_ENDPOINT))
    socket.bind(SERVER_ENDPOINT)

    # Register the socket with a poller
    poll = zmq.Poller()
    poll.register(socket, zmq.POLLIN)

    foo = branin
    dim = 2
    m = 5
    bounds = [[-5.000001, 10], [0, 15]]
    resolutions = [0.1] * dim

    abort_count = 1000
    abort_i = 0
    while True:
        #  Wait for ready from the optimizer
        print("Waiting...")
        request = socket.recv()
        print("Received request: %s" % request)

        reply = b"invalid_request"

        #  Send reply back to client
        if request == b"initial_parameters":
            abort_i = 0

            # if foo == :
            #     pass
            # else:
            initial_params = []
            for bounds_i in bounds:
                param = random.uniform(bounds_i[0], bounds_i[1])
                initial_params.append(param)

            reply = json.dumps(initial_params).encode("utf-8")

        elif request == b"bounds":
            reply = json.dumps(bounds).encode("utf-8")

        elif request == b"resolutions":
            reply = json.dumps(resolutions).encode("utf-8")

        elif request == b"budget":
            reply = json.dumps(100).encode("utf-8")

        elif request == b"options":
            reply = json.dumps(
                {
                    "minfcall": None,
                    "maxmp": None,
                    "maxfail": 5,
                    "verbose": False,
                }
            ).encode("utf-8")

        elif request.decode("utf-8").__contains__("function:"):
            request = request.decode("utf-8").replace("function:", "")

            # Reply with the function name
            reply = request.encode("utf-8")
            if request == "branin":
                foo = branin
                dim = 2
                bounds = [[-5.000001, 10], [0, 15]]
                resolutions = [0.1] * dim
            elif request == "goldstein_price":
                foo = goldstein_price
                dim = 2
                bounds = [[-2, 2]] * 2
                resolutions = [0.1] * dim
            elif request == "hartmann":
                foo = hartmann
                dim = 3  # limited to 3 or 6
                bounds = [[0, 1]] * dim
                resolutions = [0.1] * dim
            elif request == "rosenbrock":
                foo = rosenbrock
                dim = 4  # Any number of dims
                bounds = [[-5.000001, 10]] * dim
                resolutions = [0.1] * dim
            elif request == "shekel5":
                foo = shekel
                dim = 4
                bounds = [[0, 10]] * 4
                m = 5
                resolutions = [0.1] * dim
            elif request == "shekel7":
                foo = shekel
                dim = 4
                bounds = [[0, 10]] * 4
                m = 7
                resolutions = [0.1] * dim
            elif request == "shekel10":
                foo = shekel
                dim = 4
                bounds = [[0, 10]] * 4
                m = 10
                resolutions = [0.1] * dim
            elif request == "shubert":
                foo = shubert
                dim = 2
                bounds = [[-10, 10]] * 2  # or [[-5.12, 5.12]]*2
                resolutions = [0.1] * dim
            elif request == "six_hump_camel":
                foo = six_hump_camel
                dim = 2
                bounds = [[-3, 3], [-2, 2]]
                resolutions = [0.1] * dim
            else:
                reply = b"invalid_function"
                bounds = []
                resolutions = []

        elif request == b"aborted":
            print("Abort acknowledged")
            # This message is to be ignored and is only to reset the state of
            # the server to receive another request
            reply = b"ignore"

            socket.close()
            context.term()

        elif type(json.loads(request)) == dict:
            best = json.loads(request)
            print(
                "Received best conditions: {} at {} after {} steps".format(
                    best["value"], best["parameters"], best["steps"]
                )
            )
            reply = b"ignore"
            abort_i = 0

            # socket.close()
            # context.term()

        elif type(json.loads(request)) == list:
            if foo == shekel:
                result = foo(json.loads(request), m)
            else:
                result = foo(json.loads(request))
            reply = json.dumps(result).encode("utf-8")
            abort_i += 1
        else:
            print("Invalid request: {}".format(request))

        if abort_i >= abort_count:
            abort_i = 0
            reply = b"abort"

        print("Sending reply: {}".format(reply))
        socket.send(reply)


if __name__ == "__main__":
    main()
