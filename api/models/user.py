from pydantic import *
from typing import Optional, Annotated

PyObjectId = Annotated[str, BeforeValidator(str)]

class UserModel(BaseModel):
    """
    Container for a single user record.
    """

    id: Optional[PyObjectId] = Field(alias="_id")
    name: str
    model_config = ConfigDict(
        populate_by_name=True,
        arbitrary_types_allowed=True,
        json_schema_extra={
            "example": {
                "name": "Jane Doe"
            }
        } 
    )

