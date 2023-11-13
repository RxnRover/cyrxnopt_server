from pyoptimizer_backend.OptimizerController import predict

# TODO: Rename this variable
problematic_optimizers = [
    "amlro",
    "edbop",
]


def predict_server(
    optimizer_name, prev_param, yield_value, output_dir, config, venv, obj_func
):
    if optimizer_name.lower() in problematic_optimizers:
        results = predict_faux_server(
            optimizer_name,
            prev_param,
            yield_value,
            output_dir,
            config,
            venv,
            obj_func,
        )
    else:
        results = predict(
            optimizer_name,
            prev_param,
            yield_value,
            output_dir,
            config,
            venv,
            obj_func,
        )

    return results


def predict_faux_server(
    optimizer_name, prev_param, yield_value, output_dir, config, venv, obj_func
):
    results = {
        "total_iter": config["budget"],
        "best_coords": None,
        "best_value": None,
        "best_iter": None,
        "raw_results": [],
    }

    if config["direction"] == "min":
        results["best_value"] = float("inf")
    else:
        results["best_value"] = float("-inf")

    # Loop over cycle iterations
    for i in range(config["budget"]):
        prev_param = predict(
            optimizer_name,
            prev_param,
            yield_value,
            output_dir,
            config,
            venv,
        )

        yield_value = obj_func(prev_param)

        if (
            config["direction"] == "min"
            and yield_value < results["best_value"]
        ) or (
            config["direction"] == "max"
            and yield_value > results["best_value"]
        ):
            results["best_value"] = yield_value
            results["best_coords"] = prev_param
            results["best_iter"] = i

        # Add another line to the raw results
        result_line = [x for x in prev_param].append(yield_value)
        results["raw_results"].append(result_line)

    return results
