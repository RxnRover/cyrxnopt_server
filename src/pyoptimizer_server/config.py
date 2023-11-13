import json
from typing import Any, Dict


def generate_default_config(filename: str, config_desc):
    """Generates a default configuration file.

    :param filename: Name of the config file, including the path and
                     extension (.json).
    :type filename: str

    :raises OSError: Failed to generate the configuration file.
    """

    config = {}
    for option in config_desc:
        option_name = str(option["name"])
        option_type = str(option["type"]).lower()
        option_value = option["value"]

        default_value = option_value
        if isinstance(option_value, list) and option_type.find("list") == -1:
            default_value = option_value[0]

        # Entries that are prefixed by "continuous" or "categorical" need
        # to be split up
        # if "continuous" in option_name or "categorical" in option_name:
        #     name_parts = option_name.split("_")
        #     if not name_parts[0] in config:
        #         config[name_parts[0]] = {}
        #     config[name_parts[0]]["_".join(name_parts[1:])] = default_value
        # else:
        config[option_name] = default_value

    try:
        fout = open(filename, "w")
        json.dump(config, fout, indent=4)
        print("Default config file generated at: {}".format(filename))
    except OSError as e:
        print("Failed to generate config file: {}".format(filename))
        print("Please check that the path exists and file write permissions.")
        raise e
    else:
        fout.close()

    return config


def load(filename: str) -> Dict[str, Any]:
    """Load the configuration file.

    :param filename: Configuration file to load, including path.
    :type filename: str

    :raises IOError: Failed to load config file.

    :return: The loaded configuration
    :rtype: Dict[str, Any]
    """

    config = None

    print("Reading config file: {}".format(filename))

    # Try to load config
    try:
        fin = open(filename, "r")
        config = json.load(fin)
    except IOError as e:
        # TODO: These outputs should probably be moved further up the call
        #       chain
        print("Failed to load config file: {}".format(filename))
        print(
            "Please ensure the config file exists and there are no spelling"
            " errors."
        )
        print(
            "To create a config file with default values, run the program "
            "again with the --default-config flag.\n"
        )
        raise e
    else:
        fin.close()

    return config


if __name__ == "__main__":
    """Short test of generating and reading a default config file"""

    # TODO: Move this test into an actual unit test
    import os

    test_file = "./test_config.json"

    generate_default_config(test_file)
    print(load(test_file))
    os.remove(test_file)
