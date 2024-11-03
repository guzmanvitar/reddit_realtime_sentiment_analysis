"""Helper functions for the project"""

import argparse


def str2bool(input) -> bool:
    """Helper function for argparse boolean parameters

    As suggested in
    https://stackoverflow.com/questions/15008758/parsing-boolean-values-with-argparse

    Args:
        input: user command line input

    Returns:
        bool: input converted to True or False
    """
    if isinstance(input, bool):
        return input
    if input.lower() in ("yes", "true", "t", "y", "1"):
        return True
    elif input.lower() in ("no", "false", "f", "n", "0"):
        return False
    else:
        raise argparse.ArgumentTypeError("Boolean value expected.")
