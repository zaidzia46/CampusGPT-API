from pydantic import BaseModel


class FacultySubmitRequest(BaseModel):
    topic:      str
    detail:     str
    tags:       str = ""
    file_url:   str = ""