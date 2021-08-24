import pytest

from zeversolarlocal.api import (
    SolarData,
    ZeverError,
    _convert_to_string,
    _parse_content,
    default_url,
    httpx_get_client,
    solardata,
)


def test_convert_to_string():
    result = _convert_to_string(b"abc")

    assert result == "abc"


def test_parse_incoming_success():
    incoming = "1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.14 OK Error"

    result = _parse_content(incoming)

    assert result == SolarData(3.14, 1185)


@pytest.mark.parametrize(
    "incoming",
    [
        "1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185",  # too short
        "1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.a4 OK Error",  # wrong float
        "1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1a85 3.14 OK Error",  # wrong int
    ],
)
def test_parse_fail_incorrect_incoming(incoming):
    with pytest.raises(ZeverError):
        _parse_content(incoming)


@pytest.mark.asyncio
async def test_connection_timeout():
    ip_addr = "http://192.168.188.29/home.html"

    with pytest.raises(ZeverError):
        await httpx_get_client(ip_addr, 0.5)


def test_default_url():
    ip = "192.168.1.12"

    result = default_url(ip)

    assert result == "http://192.168.1.12/home.cgi"


@pytest.mark.asyncio
async def test_solardata():
    async def a_get_client(url: str, *args, **kwargs):
        return b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.14 OK Error"

    result = await solardata("fakeurl", client=a_get_client)

    assert isinstance(result, SolarData)
