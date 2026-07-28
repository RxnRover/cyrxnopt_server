.. image:: https://img.shields.io/badge/Documentation-grey
    :alt: Documentation link
    :target: https://rxnrover.github.io/cyrxnopt_server/

.. image:: https://img.shields.io/badge/-PyScaffold-005CA0?logo=pyscaffold
    :alt: Project generated with PyScaffold
    :target: https://pyscaffold.org/

.. image:: https://img.shields.io/badge/Python-3.9-blue
    :alt: Documentation link
    :target: https://rxnrover.github.io/CyRxnOpt/

#################
 cyrxnopt_server
#################

    Example benchmarking harness for `CyRxnOpt
    <https://github.com/RxnRover/CyRxnOpt>`__ algorithm testing.

This project provides a ZeroMQ-based client/server pair for benchmarking
optimization algorithms via CyRxnOpt against a shared set of benchmarking
functions. Analytical functions can be found in the `benchmarking repository
<https://github.com/RxnRover/benchmarking>`__ Real chemical reaction datasets
are used from `cyrxnopt_datasets
<https://github.com/RxnRover/cyrxnopt_datasets>`__, interpolated from recorded
reaction data. The server (``run_server``) hosts the objective functions and
answers optimizer queries while the client (``run_client``) drives a CyRxnOpt
optimizer through training and prediction cycles against the server and records
the results.

**************
 Installation
**************

This project requires Python 3.9, which is currently the only version compatible
with all of the optimizers it benchmarks.

Clone the repository and install it with pip:

.. code-block:: bash

    git clone https://github.com/RxnRover/cyrxnopt_server.git
    cd cyrxnopt_server
    pip install .

**************
 Benchmarking
**************

Some of the server's benchmarking functions interpolate real reaction data (like
``imine``, ``pk1``, ``pk2``, and ``sugar_data_yield``). The CSV datasets for
these live in a separate repository, `cyrxnopt_datasets
<https://github.com/RxnRover/cyrxnopt_datasets/tree/main/datasets>`__. Clone it
and point ``run_server`` at the ``datasets`` directory:

.. code-block:: bash

    git clone https://github.com/RxnRover/cyrxnopt_datasets.git

First, start the server, pointing it at the dataset directory:

.. code-block:: bash

    run_server -d cyrxnopt_datasets/datasets

Then, in a separate terminal, run the client against it with the optimizer and
functions to benchmark. For example, the following runs the ``random`` optimizer
against the mix of synthetic and dataset-backed functions used in the first
CyRxnOpt paper, outputting results to the ``data/random_optimizer`` directory:

.. code-block:: bash

    run_client random data/random_optimizer \
        branin goldstein_price hartmann{3,6}D rosenbrock shekel{5,7,10} shubert six_hump_camel pk1 pk2 sugar_data_yield imine \
        -p 100 -c 100 -cs 0 -t 0

Where the arguments represent the following:

- ``random`` is the optimizer to benchmark (must be supported by CyRxnOpt's
  ``OptimizerController``).
- ``data/2026-07-16_random_optimizer`` is the output directory where the
  optimizer's virtual environment, configuration, and per-round results are
  written.
- The analytical functions are ``branin goldstein_price hartmann{3,6}D
  rosenbrock shekel{5,7,10} shubert six_hump_camel``.
- The reaction datsets are ``pk1 pk2 sugar_data_yield imine``.
- ``-p 100`` is the number of prediction steps to perform per optimization
  campaign.
- ``-c 100`` is the number of campaigns to run the optimizer on each function.
- ``-cs 0`` is the starting cycle number, used to number the output directories.
- ``-t 0`` is the number of training steps to perform per cycle (``0`` skips
  training since ``random`` doesn't need training).

Run ``run_client --help`` and ``run_server --help`` for the full list of
options.

.. _pyscaffold-notes:

Making Changes & Contributing
=============================

This project uses pre-commit_, please make sure to install it before making any
changes:

.. code-block:: bash

    # After cloning the repository
    pip install pre-commit
    cd cyrxnopt_server
    pre-commit install

.. _pre-commit: https://pre-commit.com/
