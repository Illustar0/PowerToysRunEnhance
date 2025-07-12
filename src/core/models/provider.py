from collections import deque
from typing import Optional, List, Any

from pydantic import BaseModel, model_validator

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
    provider_name_tr: str | None = None
    provider_process_name: List[str]
    required_config: Optional[str]
    config_model: type[BaseModel]
    setting_group: Optional[type[Any]] = None  #

    @model_validator(mode="after")
    def set_default_translation(self):
        if self.provider_name_tr is None:
            self.provider_name_tr = self.provider_name
        return self

    class Config:
        arbitrary_types_allowed = True
