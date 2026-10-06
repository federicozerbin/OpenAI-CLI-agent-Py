import argparse
import os
import sys
import json
import subprocess

def skillHandle(call):
    args = json.loads(call.function.arguments)


