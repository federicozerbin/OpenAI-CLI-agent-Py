from app.tools import toolHandle
from app.skills import skillHandle, runSkill
import sys

def startAgent(client, model, messages, TOOLS, skills):
    while True:
            chat = client.chat.completions.create(
                model=model,
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
                functionParameters = call.function.parameters

                if functionName == "Skill":
                    result = runSkill(client, model, TOOLS, skills, functionParameters)
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
    