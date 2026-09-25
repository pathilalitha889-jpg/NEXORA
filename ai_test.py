

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI()

response = client.responses.create(
    model="gpt-5.6-luna",
    input="Say hello to NEXORA in one short sentence."
)

print(response.output_text)