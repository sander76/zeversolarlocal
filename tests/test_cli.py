from zeversolarlocal import cli
from zeversolarlocal.__main__ import _parse_args
from zeversolarlocal.api import SolarData


def test_parse_args():
    input = ["192.168.1.12"]

    result = _parse_args(input)

    assert result.ipaddress == "192.168.1.12"


def test_cli(monkeypatch):
    data = SolarData(10, 10)

    async def update(*args, **kwargs):
        return data

    monkeypatch.setattr(cli.zeversolarlocal, "solardata", update)
    args = _parse_args(["192.168.1.12"])

    result = cli.get(args)
    assert result == data
