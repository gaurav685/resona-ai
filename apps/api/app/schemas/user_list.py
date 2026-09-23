from pydantic import BaseModel


class UserSummary(BaseModel):
    user_id: str
    n_events: int


class UserListResponse(BaseModel):
    users: list[UserSummary]
