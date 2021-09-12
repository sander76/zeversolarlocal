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
    fix,
    inverter_id,
    solardata,
)


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


@pytest.mark.parametrize(
    "incoming,expected",
    [
        (
            b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.14 OK Error",
            SolarData(3.14, 1185),
        ),
        (
            b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.5 OK Error",
            SolarData(3.05, 1185),
        ),
        (
            b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.50 OK Error",
            SolarData(3.50, 1185),
        ),
    ],
)
def test_parse_incoming_success(incoming, expected):

    result = _parse_content(incoming)

    assert result == expected


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


def test_parse_zever_id_success():
    result = _parse_zever_id(
        b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1 1 ZS150060118C0109 1185 3.14 OK Error"
    )

    assert result == "ZS150060118C0109"


def test_parse_zever_id_fail():
    with pytest.raises(ZeverError):
        _parse_zever_id(
            b"1 1 EAB9618C1399 AWWQBBWVVXDJWVXF M11 18625-797R+17829-719R 12:41 24/08/2021 1"
        )


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


@pytest.mark.parametrize(
    "incoming,expected",
    [(b"10.5", b"10.05"), (b"10.05", b"10.05"), (b"0.01", b"0.01"), (b"0.1", b"0.01")],
)
def test_fix(incoming, expected):

    result = fix(incoming)
    assert result == expected
