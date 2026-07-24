from pydantic import BaseModel, Field
from typing import Optional


class RoomBase(BaseModel):
    code: str = Field(..., example="604")
    type: str = Field("classroom", example="computer_lab")  # classroom, computer_lab, gpu_lab
    capacity: int = Field(60, ge=1, le=500)
    floor: int = Field(6, ge=0, le=10)
    block: str = Field("U-Block", example="U-Block")


class RoomCreate(RoomBase):
    dept_id: Optional[int] = None


class RoomResponse(RoomBase):
    id: int
    dept_id: Optional[int] = None

    class Config:
        from_attributes = True
