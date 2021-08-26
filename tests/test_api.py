import pytest

from zeversolarlocal.api import (
    ClientAdapter,
    HttpxClient,
    SolarData,
    ZeverError,
    ZeverTimeout,
    _convert_to_string,
    _parse_content,
    _parse_zever_id,
    client_factory,
    default_url,
    inverter_id,
    solardata,
)


@pytest.fixture
def incoming():
    return b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.14 OK Error"


class DummyTestClient(ClientAdapter):
    async def get(self, url, timeout=2):
        return b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.14 OK Error"


@pytest.fixture
def dummyclientadapter():
    return DummyTestClient()


def test_convert_to_string():
    result = _convert_to_string(b"abc")

    assert result == "abc"


def test_default_url():
    ip = "192.168.1.12"

    result = default_url(ip)

    assert result == "http://192.168.1.12/home.cgi"


def test_parse_incoming_success(incoming: bytes):

    result = _parse_content(incoming)

    assert result == SolarData(3.14, 1185)


@pytest.mark.parametrize(
    "incoming_fail",
    [
        b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185",  # too short
        b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.a4 OK Error",  # wrong float
        b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1a85 3.14 OK Error",  # wrong int
    ],
)
def test_parse_fail_incorrect_incoming(incoming_fail):
    with pytest.raises(ZeverError):
        _parse_content(incoming_fail)


@pytest.mark.asyncio
async def test_httpx_timeout():
    fake_url = "http://fake_url_/"
    httpx_adapter = HttpxClient()

    with pytest.raises(ZeverTimeout):
        await httpx_adapter.get(fake_url, timeout=0.5)


def test_parse_zever_id_success(incoming):
    result = _parse_zever_id(incoming)

    assert result == "ZS150060118C0109"


@pytest.mark.asyncio
async def test_solardata_endpoint(dummyclientadapter: DummyTestClient):
    """Integration test. Getting solar data."""

    result = await solardata("fakeurl", client=dummyclientadapter)

    assert isinstance(result, SolarData)


@pytest.mark.asyncio
async def test_zever_id_endpoint(dummyclientadapter: DummyTestClient):
    """Integration test. Getting zever inverter id."""

    result = await inverter_id("fakeurl", client=dummyclientadapter)

    assert result == "ZS150060118C0109"


def test_client_factory_default():
    client = client_factory(None)

    assert isinstance(client, HttpxClient)


def test_client_factory_custom(dummyclientadapter):
    client = client_factory(dummyclientadapter)

    assert client == dummyclientadapter
