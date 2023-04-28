import argparse
import json
import os
import subprocess
import sys
from typing import Any, Dict

from pyoptimizer_backend.OptimizerController import get_optimizer
from pyoptimizer_backend.VenvManager import VenvManager

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
    if optimizer == "AMLRO":
        config["param_init"] = initial_parameters
        config["continuous Feature_Bounds"] = bounds
        config["continuous Feature_resoultions"] = resolutions
        config["budget"] = budget
    else:
        config["param_init"] = initial_parameters
        config["bounds"] = bounds
        config["resolutions"] = resolutions
        config["budget"] = budget

    return config


def parse_args() -> argparse.Namespace:
    """Parse command line arguments"""

    parser = argparse.ArgumentParser()

    # parser.add_argument(
    #     "config_file", help="Location of the configuration file to use."
    # )
    parser.add_argument("output_dir", help="Location for output data.")
    parser.add_argument("optimizer", help="Optimizer to use.")
    parser.add_argument(
        "--default-config",
        action="store_true",
        help=(
            "Generate config file with default values at the location given by"
            " output_dir."
        ),
    )

    args = parser.parse_args()

    return args


def main():
    """Starting point for using an optimizer with zmq"""

    args = parse_args()

    ROUND_COUNT = 100
    # TRAINING_STEPS = 20  # For when we use an algorithm that requires
    #                      # training

    # Set up virtual environment
    venv_m = VenvManager(
        os.path.join(args.output_dir, "venv_{}".format(args.optimizer))
    )
    if not venv_m.is_venv():
        venv_m.install_virtual_env()
        venv_m.pip_install_r("./requirements.txt")
        subprocess.call([venv_m.virtual_python, __file__] + sys.argv[1:])
        exit(0)

    # Clear results file
    with open(os.path.join(args.output_dir, "results.txt"), "w") as fout:
        fout.write("")

    # Get the requested optimizer to use
    opt = get_optimizer(args.optimizer, venv_m)

    # Install the optimizer if it is not already installed
    if not opt.check_install():
        opt.install()

    config_file = os.path.join(args.output_dir, "recent_config.json")

    # Optionally generate a default config file
    if args.default_config:
        raise RuntimeError("--default-config flag not yet supported.")
        # cfg.generate_default_config(
        #     os.path.join(args.output_dir, "recent_config.json"),
        #     opt.get_config()
        # )
    if not os.path.exists(config_file):
        config = cfg.generate_default_config(config_file, opt.get_config())
    else:
        # Read the config
        # TODO: This should eventually come from the remote socket
        config = cfg.load(config_file)

    print("Using configuration: {}".format(config))

    # address = config["ip_address"] + ":" + config["port"]
    address = "tcp://localhost:5555"
    socket = zmq_helpers.init_socket(address)

    # opt.set_config(args.output_dir, config)

    obj_func = zmq_obj_function(socket, config["direction"])

    results = None

    foos = [
        "branin",
        "goldstein_price",
        "hartmann",
        "rosenbrock",
        "shekel5",
        "shekel7",
        "shekel10",
        "shubert",
        "six_hump_camel",
    ]
    for foo in foos:
        for round in range(ROUND_COUNT):
            with open(
                os.path.join(args.output_dir, "results.txt"), "a"
            ) as fout:
                fout.write("\n\n")
                fout.write(
                    "********** {}, Round {} **********".format(foo, round + 1)
                )
                fout.write("\n\n")

            print("Setting function to: {}".format(foo))
            socket.send("function:{}".format(foo).encode("utf-8"))
            foo_resp = socket.recv().decode("utf-8")
            print("Function response: {}".format(foo_resp))
            assert foo_resp == foo

            config = initial_handshake(socket, config, args.optimizer)
            print(config)
            opt.set_config(args.output_dir, config)

            # Write initial config information
            config = cfg.load(config_file)
            with open(
                os.path.join(args.output_dir, "results.txt"), "a"
            ) as fout:
                fout.write(
                    "Initial settings:\n{}".format(
                        json.dumps(config, indent=4)
                    )
                )
                fout.write("\n\n")

            # Run the prediction
            try:
                results = opt.predict([], 0, args.output_dir, config, obj_func)
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
            elif args.optimizer == "SQSnobFit":
                result_json = json.dumps(
                    {
                        "value": results[0].optval,
                        "parameters": results[0].optpar.tolist(),
                        "steps": len(results[1]),
                    }
                ).encode("utf-8")

            socket.send(result_json)
            socket.recv()

            print(
                "Results for {}, round {}:\n{}".format(foo, round + 1, results)
            )

            print("")
            print("*" * 40)
            print("")

            write_results(results, args.output_dir, args.optimizer)


def write_results(results, output_dir, optimizer):
    res_dict = {
        "best_coords": "N/A",
        "best_value": "N/A",
        "best_iter": "N/A",
        "total_iter": "N/A",
        "message": "N/A",
        "raw_results": "N/A",
    }
    if optimizer.lower() == "nmsimplex":
        res_dict["best_coords"] = results.x
        res_dict["best_value"] = results.fun
        res_dict["best_iter"] = results.nit
        res_dict["total_iter"] = results.nit
        res_dict["message"] = results.message
    elif optimizer.lower() == "sqsnobfit":
        res_dict["best_coords"] = results[0].optpar.tolist()
        res_dict["best_value"] = results[0].optval
        # res_dict["best_iter"] = "N/A"
        res_dict["total_iter"] = len(results[1])
        # res_dict["message"] = results.message

    string = "Results:\n"
    string += "  Best coordinates:   {}\n".format(res_dict["best_coords"])
    string += "  Best value:         {}\n".format(res_dict["best_value"])
    string += "  Iterations to best: {}\n".format(res_dict["best_iter"])
    string += "  Total iterations:   {}\n".format(res_dict["total_iter"])
    string += "  Message:            {}\n".format(res_dict["message"])

    with open(os.path.join(output_dir, "results.txt"), "a") as fout:
        fout.write(string)


if __name__ == "__main__":
    main()
