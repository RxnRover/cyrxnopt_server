from pyoptimizer_server.helpers.get_optimizer import get_optimizer


def install(optimizer: str):
    opt_obj = get_optimizer(optimizer)

    opt_obj.install()
