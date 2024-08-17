from pydantic import BaseModel, Field


class FiveFourModelOutput(BaseModel):
    speaker: str = Field(..., description="The speaker of the transcript entries")
    speakers_understanding: str = Field(
        ..., description="The speaker's understanding on the topic."
    )
    other_hosts_understanding: str = Field(
        ..., description="The other hosts' understanding on the topic."
    )
    impactful_quotes: list[str] = Field(
        ...,
        description="The impactful quotes from the transcript entries. What are the most "
        "important quotes from the transcript entries?",
    )
    reasoning: str = Field(
        ...,
        description=(
            "What does the user want to know, and what does the previous context "
            "tell you?"
        ),
    )
    message: str = Field(
        ...,
        description=(
            "The message to be displayed to the user. Include impactful quotes, "
            "reasoning, and any other relevant information."
            "Format the text as markdown text to make the message more readable. Don't "
            "include a message title."
        ),
    )
