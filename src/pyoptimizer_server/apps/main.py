import argparse
import json
import os
from typing import Any, Dict

from pyoptimizer_backend.NestedVenv import NestedVenv
from pyoptimizer_backend.OptimizerController import (
    check_install,
    get_config,
    install,
    predict,
    set_config,
)

import pyoptimizer_server.config as cfg
from pyoptimizer_server.AbortException import AbortException
from pyoptimizer_server.helpers import zmq_helpers
from pyoptimizer_server.zmq_obj_function import zmq_obj_function


def initial_handshake(
    socket, config: Dict[str, Any], optimizer
) -> Dict[str, Any]:
    """Performs the initial handshake that get initialization data before
    starting the optimization.
    """

    # Request initial parameters
    print("Sending initial_parameters request")
    socket.send(b"initial_parameters")

    # Receive initial parameters
    reply = socket.recv()
    initial_parameters = json.loads(reply)
    print("Initial parameters received: {}".format(initial_parameters))

    # Request bounds
    print("Sending bounds request")
    socket.send(b"bounds")

    # Receive bounds
    reply = socket.recv()
    bounds = json.loads(reply)
    print("Bounds received: {}".format(bounds))

    # Request resolutions
    print("Sending resolutions request")
    socket.send(b"resolutions")

    # Receive resolutions
    reply = socket.recv()
    resolutions = json.loads(reply)
    print("Resolutions received: {}".format(resolutions))

    # Request budget
    print("Sending budget request")
    socket.send(b"budget")

    # Receive budget
    reply = socket.recv()
    budget = json.loads(reply)
    print("Budget received: {}".format(budget))

    # Confirm receipt
    print("Sending options request")
    socket.send(b"options")

    # Receive options
    reply = socket.recv()
    options = json.loads(reply)
    print("options received: {}".format(options))

    # Set the options in the configuration
    config["param_init"] = initial_parameters
    config["continuous"]["bounds"] = bounds
    config["continuous"]["resolutions"] = resolutions
    config["budget"] = 1000

    if optimizer == "NMSimplex":
        config["xatol"] = 0.01

    return config


# def parse_args() -> argparse.Namespace:
#     """Parse command line arguments"""

#     parser = argparse.ArgumentParser()

#     # parser.add_argument(
#     #     "config_file", help="Location of the configuration file to use."
#     # )
#     parser.add_argument("output_dir", help="Location for output data.")
#     parser.add_argument("optimizer", help="Optimizer to use.")
#     parser.add_argument(
#         "--default-config",
#         action="store_true",
#         help=(
#             "Generate config file with default values at the location given"
#             " by output_dir."
#         ),
#     )
#     parser.add_argument(
#         "-n",
#         "--ncycles",
#         default=100,
#         type=int,
#         help=("Number of cycles to run."),
#     )

#     args = parser.parse_args()

#     return args


def main():
    """Starting point for using an optimizer with zmq"""

    args = parse_args()

    ROUND_COUNT = args.cycles
    # TRAINING_STEPS = 20  # For when we use an algorithm that requires
    #                      # training

    # Set up virtual environment
    venv_dir = os.path.join(args.data_dir, "venv_{}".format(args.optimizer))
    venv_m = NestedVenv(venv_dir)
    if not os.path.exists(venv_dir):
        print("Creating virtual environment at:", venv_dir)
        venv_m.create()
    print("Activating virtual environment at:", venv_dir)
    venv_m.activate()

    # Install the optimizer if it is not already installed
    if not check_install(args.optimizer, venv_m):
        install(args.optimizer, venv_m)

    config_file = os.path.join(args.data_dir, "recent_config.json")

    # Optionally generate a default config file
    # if args.default_config:
    #     raise RuntimeError("--default-config flag not yet supported.")
    #     # cfg.generate_default_config(
    #     #     os.path.join(args.data_dir, "recent_config.json"),
    #     #     opt.get_config()
    #     # )
    if not os.path.exists(config_file):
        config = cfg.generate_default_config(
            config_file, get_config(args.optimizer)
        )
    else:
        # Read the config
        # TODO: This should eventually come from the remote socket
        config = cfg.load(config_file)

    print("Using configuration: {}".format(config))

    # address = config["ip_address"] + ":" + config["port"]
    address = "tcp://localhost:5555"
    socket = zmq_helpers.init_socket(address)

    # opt.set_config(args.data_dir, config)

    obj_func = zmq_obj_function(socket, config["direction"])

    results = None

    # foos = [
    #     "beale",
    #     "booth",
    #     "branin",
    #     "bukin_n6",
    #     "eggholder",
    #     "goldstein_price",
    #     "hartmann3D",
    #     "hartmann6D",
    #     "himmelblau",
    #     "holder_table",
    #     "matyas",
    #     "rosenbrock",
    #     "schwefel2D",
    #     "schwefel3D",
    #     "shekel5",
    #     "shekel7",
    #     "shekel10",
    #     "shubert",
    #     "six_hump_camel",
    #     "sphere",
    #     "styblinski_tang_3D",
    #     "three_hump_camel",
    # ]
    for foo in args.functions:
        for round in range(ROUND_COUNT):
            round_dir = "{}_{}".format(foo, round)
            round_dir = os.path.join(args.data_dir, round_dir)
            os.makedirs(round_dir, exist_ok=True)
            results_file = os.path.join(round_dir, "results.json")

            print("Setting function to: {}".format(foo))
            socket.send("function:{}".format(foo).encode("utf-8"))
            foo_resp = socket.recv().decode("utf-8")
            print("Function response: {}".format(foo_resp))
            assert foo_resp == foo

            config = initial_handshake(socket, config, args.optimizer)
            print(config)
            set_config(args.optimizer, config, args.data_dir, venv_m)

            # Write initial config information
            config = cfg.load(config_file)
            config_file_out = os.path.join(round_dir, "config.json")
            with open(config_file_out, "w") as fout:
                fout.write(json.dumps(config, indent=4))

            # Run the prediction
            try:
                results = predict(
                    args.optimizer,
                    [],
                    0,
                    round_dir,
                    config,
                    venv_m,
                    obj_func,
                )
            except AbortException as e:
                socket.send(b"aborted")
                print(str(e))
                return

            # Send the best results
            # TODO: Not sure if this is necessary
            # if config["direction"] == "max":
            #     results.optval = -results.optval
            if args.optimizer == "NMSimplex":
                result_json = json.dumps(
                    {
                        "value": results.fun,
                        "parameters": list(results.x),
                        "steps": results.nit,
                    }
                ).encode("utf-8")
            elif args.optimizer == "NMSimplexLMFit":
                params = [
                    value
                    for value in list(results.params.valuesdict().values())
                ]
                result_json = json.dumps(
                    {
                        "value": 0,
                        "parameters": params,
                        "steps": results.nfev,
                    }
                ).encode("utf-8")
            elif args.optimizer == "SQSnobFit":
                result_json = json.dumps(
                    {
                        "value": results.optval,
                        "parameters": results.optpar.tolist(),
                        "steps": len(results.history),
                    }
                ).encode("utf-8")
            else:
                raise ValueError(
                    "Invalid optimizer name: {}".format(args.optimizer)
                )

            socket.send(result_json)
            socket.recv()

            print(
                "Results for {}, round {}:\n{}".format(foo, round + 1, results)
            )

            print("")
            print("*" * 40)
            print("")

            write_results(results, config, results_file, args.optimizer)


def write_results(results, config, results_file, optimizer):
    res_dict = {
        "best_coords": "N/A",
        "best_value": "N/A",
        "best_iter": "N/A",
        "total_iter": "N/A",
        "message": "N/A",
        "raw_results": "N/A",
    }
    if optimizer.lower() == "nmsimplex":
        res_dict["best_coords"] = results.x.tolist()
        res_dict["best_value"] = results.fun
        res_dict["best_iter"] = results.nit
        res_dict["total_iter"] = results.nit
        res_dict["message"] = results.message
        res_dict["raw_results"] = results.raw_results
    elif optimizer.lower() == "nmsimplexlmfit":
        params = [
            value for value in list(results.params.valuesdict().values())
        ]
        res_dict["best_coords"] = params
        res_dict["best_value"] = 0
        res_dict["best_iter"] = results.nfev
        res_dict["total_iter"] = results.nfev
        res_dict["message"] = results.message
    elif optimizer.lower() == "sqsnobfit":
        res_dict["best_coords"] = results.optpar.tolist()
        res_dict["best_value"] = results.optval
        res_dict["best_iter"] = find_optimum(results)
        res_dict["total_iter"] = len(results.history)
        # res_dict["message"] = results.message
        res_dict["raw_results"] = results.history.tolist()

    # Add the config options onto the results dictionary for context
    res_dict = res_dict | config

    string = "Results:\n"
    string += "  Best coordinates:   {}\n".format(res_dict["best_coords"])
    string += "  Best value:         {}\n".format(res_dict["best_value"])
    string += "  Iterations to best: {}\n".format(res_dict["best_iter"])
    string += "  Total iterations:   {}\n".format(res_dict["total_iter"])
    string += "  Message:            {}\n".format(res_dict["message"])

    with open(results_file, "w") as fout:
        fout.write(json.dumps(res_dict, indent=4))


def find_optimum(results) -> int:
    # target = results.optpar.tolist()
    target = results.optval

    for coord in results.history.tolist():
        # match = True
        # for i in len(target):
        #     match = match and target == coord[0]
        match = target == coord[0]

        if match:
            return results.history.tolist().index(coord)

    return -1


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""

    parser = argparse.ArgumentParser()

    # parser.add_argument("output_dir", help="Location for output data.")
    parser.add_argument("optimizer", help="Optimizer to use.")
    parser.add_argument(
        "data_dir", help="Location for results file to analyze."
    )
    parser.add_argument(
        "functions", nargs="+", help="Benchmarking functions to use."
    )
    parser.add_argument(
        "-c",
        "--cycles",
        default=1,
        type=int,
        help=("Number of cycles to run for the optimizer on the function."),
    )
    parser.add_argument(
        "-cs",
        "--cyclestart",
        default=0,
        type=int,
        help=(
            "The starting number for cycles to append to the data directories."
        ),
    )
    parser.add_argument(
        "-t",
        "--training-steps",
        dest="training_steps",
        default=20,
        type=int,
        help=(
            "Number of training steps to perform in each cycle if "
            "training is needed."
        ),
    )
    parser.add_argument(
        "-p",
        "--predict-steps",
        dest="predict_steps",
        default=2,
        type=int,
        help=("Number of prediction steps to perform in each cycle."),
    )

    args = parser.parse_args()

    return args


if __name__ == "__main__":
    main()
