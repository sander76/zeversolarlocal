"""Zever solar cli."""
import argparse
import asyncio

import zeversolarlocal

parser = argparse.ArgumentParser()
parser.add_argument("ipaddress")

args = parser.parse_args()


def get():
    loop = asyncio.get_event_loop()

    address = args.ipaddress

    url = f"http://{address}/home.cgi"
    print(f"Getting solar data from Zeversolar inverter located at {address}")
    solar_data = loop.run_until_complete(zeversolarlocal.solardata(url))

    print(solar_data)


get()
