from cyrxnopt.OptimizerController import train

problematic_optimizers = [
    "amlro",
    "edbop",
]


def train_server(
    optimizer_name,
    prev_param,
    yield_value,
    training_steps,
    output_dir,
    config,
    venv,
    obj_func,
):
    if optimizer_name.lower() in problematic_optimizers:
        prev_param, yield_value = train_faux_server(
            optimizer_name,
            prev_param,
            yield_value,
            training_steps,
            output_dir,
            config,
            venv,
            obj_func,
        )
    # TODO: Once we find an algorithm that uses this, we'll have to fix
    #       whatever it is returning
    # else:
    #     results = train(
    #         optimizer_name,
    #         prev_param,
    #         yield_value,
    #         training_steps,
    #         output_dir,
    #         config,
    #         venv,
    #         obj_func,
    #     )

    return prev_param, yield_value


def train_faux_server(
    optimizer_name,
    prev_param,
    yield_value,
    training_steps,
    output_dir,
    config,
    venv,
    obj_func,
):
    for i in range(training_steps):
        prev_param = train(
            optimizer_name,
            prev_param,
            yield_value,
            i,
            output_dir,
            config,
            venv,
        )

        yield_value = obj_func(prev_param)

    return prev_param, yield_value
