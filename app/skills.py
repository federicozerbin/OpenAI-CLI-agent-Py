import argparse
import os
import re
import sys
import json
import subprocess
import yaml
from app.agent import startAgent

def skillHandle(userPrompt):
    skills = loadSkills()
    systemPrompt = buildSystemPrompt(skills)
    resolvedUserPrompts = resolvePrompt(userPrompt, skills)
    return { "skills": skills, "systemPrompt": systemPrompt, "resolvedUserPrompts": resolvedUserPrompts }

#loads skills into array
def loadSkills():
    skillsDir = os.path.join(os.getcwd(), ".claude", "skills")
    if not os.path.exists(skillsDir):
        return []

    #Scan .claude/skills/, run through the skill folders and parse the frontmatter to read the name and description out of each SKILL.md,
    # and add them to your system prompt. Do not include the bodies.
    skills = []

    for entry in os.listdir(skillsDir):
        if not os.path.isdir(os.path.join(skillsDir, entry)):
            continue

        file = os.path.join(skillsDir, entry, "SKILL.md")
        if not os.path.exists(file):
            continue

        with open(file, "r") as f:
            content = f.read()
        #check if contains frontmatter between "---" and extract it
        match = content.match(r"^---\r?\n([\s\S]*?)\r?\n---\r?\n?([\s\S]*)$")
        if not match:
            continue

        #parse it to add it to the skills
        meta = yaml.safe_load(match[1]) if match[1] else {}
        skills.append({
            "name": meta.get("name") or entry,
            "description": meta.get("description") or "",
            "context": meta.get("context"),
            "body": match[2].strip() if match[2] else ""
        })
    
    return skills

#runskill searches for context, called by agent if theres a skill
def runSkill(client, model, tools, skills, params):
    name, args = params.name, params.args
    expanded = expandSkill(skills, name, args)
    if not expanded:
        return f"Error: skill '{params.name}' not found"

    #skill with no context return body
    if expanded.skill.context != "fork":
        return expanded.text

    #skill with context has a subagent
    subMessages = [{"role": "user", "content": expanded.text}]
    answer = startAgent(client, model, subMessages, tools, skills)

    return f"Skill {params.name} ran in a separate context and returned: {answer}";

def buildSystemPrompt(skills):
    list_items = [f"- {s['name']}: {s['description']}" for s in skills]
    return f"You have access to the following skills:\n\n{'\n'.join(list_items)}\n\nIf a skill matches the user's request, call the Skill tool with its name\nand follow the instructions it returns."

#builds the user prompt with positional args tokens
def resolvePrompt(prompt, skills):

    #splits prompt (each token is a skill or ARGUMENT)
    tokens = prompt.trim().split(r'\s+')
    used = []
    i = 0

    #while token starts with /, it's a skill, i push it in an array
    while i < len(tokens) and tokens[i].startswith("/"):
        skill = next((s for s in skills if s["name"] == tokens[i][1:]), None)
        if not skill:
            break
        used.append(skill)
        i += 1
    

    #if it doesn not start with / it's a user message
    if len(used) == 0:
        return [{"role": "user", "content": prompt}]

    #the rest, is shared ARGUMENT between the skills, we take
    # each skill with map and fill their body with "rest"
    rest = tokens[i:]
    return [{
        "role": "user",
        "content": fillBody(skill.body, rest),
    } for skill in used]

# fills a single body with positional token ARGUMENTS
def fillBody(body, tokens, appendArgs = True):
    args = " ".join(tokens)

    if not re.search(r'\$ARGUMENTS|\$\d+', body):
        return args and appendArgs and f"{body}\n\nARGUMENTS: {args}" or body

    return re.sub(r'\$ARGUMENTS|\$(\d+)', lambda m: args if m.group(1) is None else (tokens[int(m.group(1))] if 0 <= int(m.group(1)) < len(tokens) else ""), body)


#for subagent skill calls
def expandSkill(skills, name, args):
    skill = next((s for s in skills if s["name"] == name), None)
    if not skill:
        return None

    tokens = (args or "").strip().split() if args else []
    return { "skill": skill, "text": fillBody(skill["body"], tokens, skill["context"] != "fork") }


