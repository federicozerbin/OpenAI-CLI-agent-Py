import argparse
import os
import sys
import json

from openai import OpenAI
from app.tools import toolHandle

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [{"role": "user", "content": args.p}]

    chat = client.chat.completions.create(
        model="anthropic/claude-haiku-4.5",
        messages=[{"role": "user", "content": args.p}],
        tools=[{
                 "type": "function",
                 "function": {
                   "name": "Read",
                   "description": "Read and return the contents of a file",
                   "parameters": {
                     "type": "object",
                     "properties": {
                       "file_path": {
                         "type": "string",
                         "description": "The path to the file to read"
                       }
                     },
                     "required": ["file_path"]
                   }
                 }
               }
        ]
    )

    if not chat.choices or len(chat.choices) == 0:
        raise RuntimeError("no choices in response")

    assistantMessage = chat.choices[0].message
    messages.append(assistantMessage)

    toolCalls = chat.choices[0].message.tool_calls

    if not toolCalls:
        print(assistantMessage.content)
        return

    for call in toolCalls:
        functionName = call.function.name;
        result = ""
        try:
            if functionName == "Skill":
                #future subagent call
                pass #result = await runSkill(client, model, tools, skills, functionParameters);
            else:
                #normal call
                result = toolHandle(call)
        except Exception as e:
            print("Tool error:", functionName, e, file=sys.stderr)
            result = f"Error: {e}"

        messages.append({
            role: "tool",
            tool_call_id: call.id,
            content: str(result),
        })

        print(result)
        return

    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

if __name__ == "__main__":
    main()
