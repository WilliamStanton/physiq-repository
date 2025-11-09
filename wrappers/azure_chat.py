import os
import json
import time

from dotenv import load_dotenv
from openai import APIError, APITimeoutError, AzureOpenAI

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
)

DEPLOYMENT_NAME = os.getenv("AZURE_OPENAI_DEPLOYMENT")

def llm(
    user_message,
    system_message: str = "You are a helpful fitness AI coach.",
    temperature: float = 0.2,
    retries: int = 3,
    retry_delay: float = 2.0,
):
    messages = [{"role": "system", "content": system_message}]

    if isinstance(user_message, str):
        messages.append({"role": "user", "content": user_message})
    elif isinstance(user_message, list):
        messages.extend(user_message)
    else:
        raise ValueError("user_message must be a string or list of messages")

    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=DEPLOYMENT_NAME,
                messages=messages,
                temperature=temperature,
            )

            ai_reply = response.choices[0].message.content.strip()

            # Try to parse as JSON, fallback to string
            try:
                return json.loads(ai_reply)
            except json.JSONDecodeError:
                return ai_reply

        except (APIError, APITimeoutError, ConnectionError) as e:
            print(f"[AzureOpenAI] Error: {e} (attempt {attempt + 1}/{retries})")
            if attempt < retries - 1:
                time.sleep(retry_delay * (2**attempt))
                continue
            return {"error": f"AI request failed after {retries} attempts: {str(e)}"}
        except Exception as e:
            print(f"[AzureOpenAI] Unexpected error: {e}")
            return {"error": str(e)}

    return None
