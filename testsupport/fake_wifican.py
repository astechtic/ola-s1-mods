#!/usr/bin/env python3
"""A fake `wifican.WifiCanRpc` gRPC daemon — the scooter's root RPC, on localhost.

It implements the one method ola.py calls, `/wifican.WifiCanRpc/ExecuteADBCommand`,
with the exact hand-rolled wire format ola.py uses: the request carries the command
as protobuf field 1 (string); the reply carries field 1 = status and field 2 = output.
Commands are executed against a FakeAndroid, so ola.py talks to it end-to-end over a
real gRPC channel with no scooter.
"""
from __future__ import annotations

from concurrent import futures

import grpc

from .fake_android import FakeAndroid

_METHOD = "/wifican.WifiCanRpc/ExecuteADBCommand"


def _read_varint(buf: bytes, i: int) -> tuple[int, int]:
    value = shift = 0
    while i < len(buf):
        b = buf[i]
        i += 1
        value |= (b & 0x7F) << shift
        if not b & 0x80:
            break
        shift += 7
    return value, i


def _varint(n: int) -> bytes:
    out = bytearray()
    while True:
        b = n & 0x7F
        n >>= 7
        out.append(b | 0x80 if n else b)
        if not n:
            return bytes(out)


def _decode_request(buf: bytes) -> str:
    """Pull the command string out of field 1 (wire type 2) of the request."""
    i = 0
    while i < len(buf):
        key, i = _read_varint(buf, i)
        field, wire = key >> 3, key & 7
        if wire == 2:
            length, i = _read_varint(buf, i)
            chunk = buf[i:i + length]
            i += length
            if field == 1:
                return chunk.decode("utf-8", "replace")
        elif wire == 0:
            _, i = _read_varint(buf, i)
        else:
            break
    return ""


def _encode_response(status: int, message: str) -> bytes:
    raw = message.encode()
    return (_varint((1 << 3) | 0) + _varint(status)
            + _varint((2 << 3) | 2) + _varint(len(raw)) + raw)


class _Handler(grpc.GenericRpcHandler):
    def __init__(self, device: FakeAndroid):
        self.device = device

    def service(self, handler_call_details):
        if handler_call_details.method != _METHOD:
            return None

        def handle(request: bytes, context) -> bytes:
            command = _decode_request(request)
            status, output = self.device.execute_line(command)
            return _encode_response(status, output)

        return grpc.unary_unary_rpc_method_handler(
            handle,
            request_deserializer=lambda b: b,
            response_serializer=lambda b: b,
        )


def start(device: FakeAndroid | None = None, host: str = "127.0.0.1"):
    """Start the daemon on a free port. Returns (server, port, device)."""
    device = device or FakeAndroid()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=4))
    server.add_generic_rpc_handlers((_Handler(device),))
    port = server.add_insecure_port(f"{host}:0")
    server.start()
    return server, port, device


if __name__ == "__main__":
    srv, port, _ = start()
    print(f"fake wifican daemon on 127.0.0.1:{port}  (Ctrl-C to stop)")
    try:
        srv.wait_for_termination()
    except KeyboardInterrupt:
        srv.stop(0)
