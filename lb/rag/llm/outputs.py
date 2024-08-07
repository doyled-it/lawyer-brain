from pydantic import BaseModel, Field


class FiveFourModelOutput(BaseModel):
    speaker: str = Field(..., description="The speaker of the transcript entry.")
    speakers_understanding: str = Field(
        ..., description="The speaker's understanding on the topic."
    )
    other_hosts_understanding: str = Field(
        ..., description="The other hosts' understanding on the topic."
    )
    reasoning: str = Field(
        ...,
        description=(
            "What does the user want to know, and what does the previous context "
            "tell you?"
        ),
    )
    message: str = Field(..., description="The message to be displayed to the user")
