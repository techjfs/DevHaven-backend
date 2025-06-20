from pydantic import WrapSerializer
from datetime import datetime
from typing import Annotated, Any


def convert_to_timestamp(value: Any, handler) -> int:
    return int(value.timestamp())


Datetime2Timestamp = Annotated[datetime, WrapSerializer(convert_to_timestamp)]
