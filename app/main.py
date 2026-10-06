import argparse
import os
import sys
import yaml

testo = """
name: commit
description: Crea un commit
tags: [git, utils]
"""

dati = yaml.safe_load(testo)
print(dati["name"])   # commit
print(dati["tags"])   # ['git', 'utils']

from openai import OpenAI
from app.tools import toolHandle
from app.skills import skillHandle

API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL", default="https://openrouter.ai/api/v1")

TOOLS = [{
    "type": "function",
    "function": {
        "name": "Read",
        "description": "Read and return the contents of a file",
        "parameters": {
            "type": "object",
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "The path to the file to read",
                }
            },
            "required": ["file_path"],
        },
    },
},
{
  "type": "function",
  "function": {
    "name": "Write",
    "description": "Write content to a file",
    "parameters": {
      "type": "object",
      "required": ["file_path", "content"],
      "properties": {
        "file_path": {
          "type": "string",
          "description": "The path of the file to write to"
        },
        "content": {
          "type": "string",
          "description": "The content to write to the file"
        }
      }
    }
  }
},
{
  "type": "function",
  "function": {
    "name": "Bash",
    "description": "Execute a shell command",
    "parameters": {
      "type": "object",
      "required": ["command"],
      "properties": {
        "command": {
          "type": "string",
          "description": "The command to execute"
        }
      }
    }
  }
}
]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("-p", required=True)
    args = p.parse_args()

    if not API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY is not set")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL)

    messages = [{"role": "user", "content": prompt}]

    while True:
        chat = client.chat.completions.create(
            model="anthropic/claude-haiku-4.5",
            messages=messages,
            tools=TOOLS,
        )

        if not chat.choices:
            raise RuntimeError("no choices in response")

        assistantMessage = chat.choices[0].message
        messages.append(assistantMessage)

        toolCalls = assistantMessage.tool_calls

        if not toolCalls:
            print(assistantMessage.content)
            return

        for call in toolCalls:
            functionName = call.function.name
            if functionName == "Skill"
                skills = skillHandle(call)
            try:
                result = toolHandle(call)
            except Exception as e:
                print("Tool error:", functionName, e, file=sys.stderr)
                result = f"Error: {e}"

            messages.append({
                "role": "tool",
                "tool_call_id": call.id,
                "content": str(result),
            })


if __name__ == "__main__":
    main()