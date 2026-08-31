# engine.py

from openai import OpenAI
import os
from dotenv import load_dotenv
from schemas import Ticket, TicketRequestModel
from typing import List
from pydantic import ValidationError
import json
from json import JSONDecodeError

class ExtractionFailedException(Exception):
    pass

load_dotenv()
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
if not DEEPSEEK_API_KEY:
    raise ValueError("DEEPSEEK_API_KEY is NOT present in the Environment Variables.")
print("DEEPSEEK_API_KEY loaded.")

client = OpenAI(
    base_url="https://api.deepseek.com",
    api_key=DEEPSEEK_API_KEY
)

sys_prompt_content = """
You are a support ticket extraction system. You will receive a raw, unstructured support ticket. Extract the relevant information and output ONLY a single valid JSON object — no explanation, no markdown code fences, no text before or after the JSON.

The JSON must match this exact structure:

{
  "customer_name": <string or null — use null if no name is mentioned>,
  "issue_category": <one of exactly: "billing", "shipping", "technical", "account_access", "product_defect", "refund_request", "general_inquiry", "misc">,
  "urgency": <one of exactly: "High", "Medium", "Low">,
  "order": {
    "order_id": <string or null — use null if not mentioned or unclear>,
    "product": <one of exactly: "wireless_earbuds", "standing_desk_converter", "robot_vacuum", "smart_blender", "noise_cancelling_headphones", "portable_monitor", "ergonomic_keyboard", "air_purifier", "misc">,
    "purchase_date": <string or null — dates can be vague or approximate, write them as stated, e.g. "around the 12th-13th" — do not invent a precise date if the customer wasn't precise>
  },
  "summary": <string — a concise summary of the ticket>
}

Rules:
- The values for "issue_category", "urgency", and "product" MUST be exactly one of the listed options, spelled and cased exactly as shown. Do not invent new categories or use different casing.
- Even if a ticket is ambiguous or contains conflicting information, you must still pick exactly one value for "issue_category" and "urgency" — never combine, split, or leave these blank. Use the "summary" field to capture any ambiguity, contradiction, or nuance you weren't able to express in the fixed fields.
- If a ticket raises multiple issues, choose the single most urgent or primary issue for "issue_category", and mention the secondary issue in "summary".
- If the product mentioned doesn't match any listed option, or no product is mentioned, use "misc".
- Do not fabricate information that isn't stated or reasonably implied by the ticket text.
"""

system_prompt = [{"role": "system", 
                 "content": sys_prompt_content}]

def get_llm_response(user_prompt: List[dict]) -> str:

    messages = system_prompt + user_prompt
    response = client.chat.completions.create(messages=messages, model="deepseek-chat", response_format={"type": "json_object"})
    maybe_json = response.choices[0].message.content
    return maybe_json

def get_data(input: TicketRequestModel, max_tries: int = 3) -> Ticket:

    user_prompt = [{"role": "user", "content": input.ticket_str}]
    last_error = None
    for _ in range(max_tries):
        maybe_json = get_llm_response(user_prompt)

        try: 
            json_op = json.loads(maybe_json)

            try:
                valid_op = Ticket(**json_op)

                return valid_op

            except ValidationError as e:
                print("ValidationError Ocurred")
                last_error = str(e)
                user_prompt += [{"role": "assistant", "content": maybe_json}, 
                                {"role": "user", "content": str(e)}]

        except JSONDecodeError as e:
            print("JSONDecodeError Ocurred")
            last_error = str(e)
            user_prompt += [{"role": "assistant", "content": maybe_json},
                            {"role": "user", "content": f"{str(e)} \nThis is not a valid JSON syntax."}]

    raise ExtractionFailedException(f"Extraction failed after reaching maximum retries of {max_tries}. \nThe last error message was: {last_error}.\nThe complete prompt tracing was: {user_prompt}")