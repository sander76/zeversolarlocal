import argparse
import sys

from zeversolarlocal import cli  # noqa


def _parse_args(args):
    parser = argparse.ArgumentParser()
    parser.add_argument("ipaddress")

    args = parser.parse_args(args)
    return args


if __name__ == "__main__":
    args = _parse_args(sys.argv[1:])
    cli.get(args)
