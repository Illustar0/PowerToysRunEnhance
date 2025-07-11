from PySide6.QtCore import QLocale
from pydantic import BaseModel, Field


class CommonConfigModel(BaseModel):
    auto_focus: bool = Field(True, description="自动设置焦点")
    """自动设置焦点"""
    active_provider: str = Field("Command Palette", description="当前激活的 Provider")
    """当前激活的 Provider"""
    language: str = Field(QLocale.system().name())
    """GUI 使用的语言"""


class AppConfigModel(BaseModel):
    Common: CommonConfigModel
    Providers: dict[str, dict]
