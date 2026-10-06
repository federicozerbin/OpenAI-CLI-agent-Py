import argparse
import os
import sys
import json

def toolHandle(call):
    args = json.loads(call.function.arguments)
    if(call.function.name == "Read"):
        f = open(args["file_path"])
        print(f.read())
