import json
import random

import numpy as np
import pandas as pd
import zmq
from benchmarking.functions.beale import beale
from benchmarking.functions.booth import booth
from benchmarking.functions.branin import branin
from benchmarking.functions.bukin_n6 import bukin_n6
from benchmarking.functions.eggholder import eggholder
from benchmarking.functions.goldstein_price import goldstein_price
from benchmarking.functions.hartmann import hartmann
from benchmarking.functions.himmelblau import himmelblau
from benchmarking.functions.holder_table import holder_table
from benchmarking.functions.matyas import matyas
from benchmarking.functions.rosenbrock import rosenbrock
from benchmarking.functions.schwefel import schwefel
from benchmarking.functions.shekel import shekel
from benchmarking.functions.shubert import shubert
from benchmarking.functions.six_hump_camel import six_hump_camel
from benchmarking.functions.sphere import sphere
from benchmarking.functions.styblinski_tang import styblinski_tang
from benchmarking.functions.three_hump_camel import three_hump_camel
from data_tools.interpolate import griddata


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
    points = None
    values = None
    data_file = None

    abort_count = 10000
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
            reply = json.dumps(99).encode("utf-8")

        elif request == b"options":
            reply = json.dumps(
                {
                    "minfcall": None,
                    "maxmp": None,
                    "maxfail": 5,
                    "verbose": False,
                }
            ).encode("utf-8")

        # WARNING: This only works if the server is on the same LOCAL file
        #          system as the client right now. It should probably be
        #          switched to accept the dataframe from the client.
        elif request.decode("utf-8").__contains__("data_file:"):
            request = request.decode("utf-8").replace("data_file:", "")

            data_file = request

            reply = data_file.encode("utf-8")

        elif request.decode("utf-8").__contains__("function:"):
            request = request.decode("utf-8").replace("function:", "")

            # Reply with the function name
            reply = request.encode("utf-8")
            if request == "beale":
                foo = beale
                dim = 2
                bounds = [[-4.5, 4.5]] * dim
                resolutions = [0.1] * dim
            elif request == "booth":
                foo = booth
                dim = 2
                bounds = [[-10, 10]] * dim
                resolutions = [0.1] * dim
            elif request == "branin":
                foo = branin
                dim = 2
                bounds = [[-5.000001, 10], [0, 15]]
                resolutions = [0.1] * dim
            elif request == "bukin_n6":
                foo = bukin_n6
                dim = 2
                bounds = [[-15, -5], [-3, 3]]
                resolutions = [0.1] * dim
            elif request == "eggholder":
                foo = eggholder
                dim = 2
                bounds = [[-512, 512]] * dim
                resolutions = [0.1] * dim
            elif request == "goldstein_price":
                foo = goldstein_price
                dim = 2
                bounds = [[-2, 2]] * 2
                resolutions = [0.1] * dim
            elif request == "hartmann3D":
                foo = hartmann
                dim = 3  # limited to 3 or 6
                bounds = [[0, 1]] * dim
                resolutions = [0.1] * dim
            elif request == "hartmann6D":
                foo = hartmann
                dim = 6  # limited to 3 or 6
                bounds = [[0, 1]] * dim
                resolutions = [0.1] * dim
            elif request == "himmelblau":
                foo = himmelblau
                dim = 2
                bounds = [[-5, 5]] * dim
                resolutions = [0.1] * dim
            elif request == "holder_table":
                foo = holder_table
                dim = 2
                bounds = [[-10, 10]] * dim
                resolutions = [0.1] * dim
            elif request == "matyas":
                foo = matyas
                dim = 2
                bounds = [[-10, 10]] * dim
                resolutions = [0.1] * dim
            elif request == "rosenbrock":
                foo = rosenbrock
                dim = 4  # Any number of dims
                bounds = [[-5.000000001, 10]] * dim
                resolutions = [0.1] * dim
            elif request == "schwefel2D":
                foo = schwefel
                dim = 2
                bounds = [[-500, 500]] * dim
                resolutions = [1] * dim
            elif request == "schwefel3D":
                foo = schwefel
                dim = 3
                bounds = [[-500, 500]] * dim
                resolutions = [1] * dim
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
            elif request == "sphere":
                foo = sphere
                dim = 3
                bounds = [[-100, 100]] * dim
                resolutions = [0.1] * dim
            elif request == "styblinski_tang_3D":
                foo = styblinski_tang
                dim = 3
                bounds = [[-5, 5]] * dim
                resolutions = [0.1] * dim
            elif request == "three_hump_camel":
                foo = three_hump_camel
                dim = 2
                bounds = [[-5, 5]] * dim
                resolutions = [0.1] * dim
            elif request == "interpolate":
                foo = griddata.point
                dim = 3
                bounds = [[0.05, 3.0], [0.05, 3.0], [10, 82]]
                resolutions = [0.01, 0.01, 2.0]
                points, values = get_interpolate_data(data_file)
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
            elif data_file is not None:
                result = foo(points, values, json.loads(request))
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


def get_interpolate_data(data_file: str):
    # Loading reaction adata set
    rxn_data = pd.read_csv(data_file)
    rxn_data = rxn_data.drop(rxn_data.columns[2], axis=1)
    points = np.array(
        rxn_data.drop(rxn_data.columns[-1], axis=1).values.tolist()
    )
    values = np.array(rxn_data["Yield"].values.tolist())

    return points, values


if __name__ == "__main__":
    main()
