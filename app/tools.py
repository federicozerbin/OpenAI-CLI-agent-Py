import argparse
import os
import sys
import json

def toolHandle(call):
    args = json.loads(call.function.arguments)

    if(call.function.name == "Read"):
        f = open(args["file_path"])
        return f.read()

    if(call.function.name == "Write"):
        dir_path = os.path.dirname(args["file_path"])
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
            with open(args["file_path"], "w", encoding="utf-8") as f:
                f.write(args["content"])
                return f"file written in: {args["file_path"]}"
