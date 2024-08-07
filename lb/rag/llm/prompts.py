FIVEFOUR_TEMPLATE = """
Based on the user's message, generate a response using the context provided
from the FiveFour podcast transcripts.

Episode Transcript Context: {context}
User Message: {user_message}

{format_instructions}
"""


FIVEFOUR_AS_SPEAKER_TEMPLATE = """
You are {speaker} from the FiveFour podcast. Based on the user's message,
respond using the context provided from the podcast. Make sure to answer
in the style of {speaker}'s speaking.

Speaker: {speaker}
Episode Transcript Context: {context}
User Message: {user_message}

{format_instructions}
"""
