from pydantic import BaseModel


class InputData(BaseModel):
    msg: int
    vkCode: int
    flags: int
    time: int
    capslock: bool
