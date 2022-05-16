from typing import Optional
import grpc
from djentry.settings.common import DJENTRY_STATISTIC_BACKEND_ADDR
from backend.proto.djentry_pb2_grpc import DjentryStatisticsStub

stub_instance: Optional[DjentryStatisticsStub] = None


def GetStub() -> DjentryStatisticsStub:
    """Return a stub for the djentry statistic server"""
    # pylint: disable=global-statement
    global stub_instance
    # pylint: enable=global-statement
    if not stub_instance:
        chan = grpc.insecure_channel(DJENTRY_STATISTIC_BACKEND_ADDR)
        stub_instance = DjentryStatisticsStub(chan)
    return stub_instance
