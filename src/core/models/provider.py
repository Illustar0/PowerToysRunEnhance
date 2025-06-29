from collections import deque
from typing import Optional, List

from pydantic import BaseModel

from src.core.models import CommonConfigModel
from src.core.models import InputData


class ProviderContext:
    provider_process_name: str
    provider_path: Optional[str] = None
    provider_hwnd: Optional[int] = None
    common_config: CommonConfigModel
    provider_config: Optional[dict] = None
    user_input: Optional[deque[InputData]] = None


class ProviderMeta(BaseModel):
    provider_name: str
    provider_process_name: List[str]
    required_config: Optional[str]
