import os
from openai import OpenAI


def generate_email_with_ai(prompt: str) -> str:
    """
    Generate email using OpenAI if API key is available.
    Raises exception if key is missing or call fails.
    """

    api_key = os.getenv("OPENAI_API_KEY")

    if not api_key:
        raise Exception("OPENAI_API_KEY not set")

    client = OpenAI(api_key=api_key)

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": "You are a concise, natural B2B sales assistant.",
            },
            {"role": "user", "content": prompt},
        ],
        temperature=0.7,
    )

    return response.choices[0].message.content.strip()