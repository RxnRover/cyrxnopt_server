from pyoptimizer_backend.OptimizerABC import OptimizerABC
from pyoptimizer_backend.OptimizerAmlro import OptimizerAmlro
from pyoptimizer_backend.OptimizerNMSimplex import OptimizerNMSimplex
from pyoptimizer_backend.VenvManager import VenvManager


def get_optimizer(
    optimizer_name: str, venv: VenvManager = None
) -> OptimizerABC:
    """Get an optimizer object for the provided optimizer name. It will
    be installed in the provided virtual environment.

    :param optimizer_name: Optimizer name.
    :type optimizer_name: str
    :param venv: Virtual environment to install the optimizer into,
                 defaults to None
    :type venv: pyoptimizer_backend.VenvManager, optional

    :raises ValueError: Invalid optimizer name.

    :return: Optimizer instance for the provided name.
    :rtype: pyoptimizer_backend.OptimizerABC
    """

    # Add optimizers here in alphabetical order
    if optimizer_name == "AMLRO":
        optimizer = OptimizerAmlro(venv)
    elif optimizer_name == "NMSimplex":
        optimizer = OptimizerNMSimplex(venv)
    else:
        raise ValueError("Optimizer not recognized: {}".format(optimizer))

    return optimizer
