#!/usr/bin/env python

# Example of NextLLAKit
# Copyright (c) 2025 DiamondGotCat
# MIT License

import json
import subprocess
from rich import print
from openai import OpenAI
from main import NextLLAKit
from rich.prompt import Prompt

localVars = {}
chatHistory = []
client = OpenAI()
kit = NextLLAKit()

def runPython(script, resultVar):
    exec(script, globals(), localVars)
    result = localVars.get(resultVar)
    globals().update(localVars)
    return result

def runShellCommand(command):
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    return f"stdout: \n{result.stdout}\n\nstderr: \n{result.stderr}"

def endChat():
    print("[green]Chat session ended. Goodbye![/green]")
    raise SystemExit()

exampleAvailableCommands = [

    # runPython
    {
        "id": "runPython",
        "args": [
            "content",
            "resultVar"
        ],
        "desc": """
Execute Python Script.
You should save the result in a variable of your choice within your script.

Arguments:
- content: Python Script
- resultVar: Variable Name of Saved Result Data

Output:
- Content of resultVar
""",
        "action": runPython
    },

    # runShellCommand
    {
        "id": "runShellCommand",
        "args": [
            "command"
        ],
        "desc": """
Execute a shell command.
This command will run the provided shell command and return its standard output.

Arguments:
- command: The shell command to execute as a string.

Output:
- Standard output of the shell command execution.
""",
        "action": runShellCommand
    },

    # endChat
    {
        "id": "endChat",
        "args": [],
        "desc": """
End this Chat.
""",
        "action": endChat
    }
]

def getOneResponse(chat_history, model_id):
    response = client.chat.completions.create(model=model_id,
    messages=chat_history)
    return response.choices[0].message.content

def main(modelID):
    global kit
    global chatHistory
    current_session_id = kit.getVar("currentSessionID")["data"]
    response = getOneResponse([{"role": "system", "content": kit.getSystemPrompt()}] + chatHistory, modelID)
    result = kit.main_process(response)
    if result["data"]["isContainCommand"] == True:
        for command in result["data"]["containCommands"]:
            try:
                print("\n[bold yellow]🛠️ AgentCode Execution Request[/bold yellow]")
                print(f"Session ID: [cyan]{current_session_id}[/cyan]")
                print(f"Command ID: [blue bold]{command["id"]}[/blue bold]")
                print("\n[bold]📘 Description:[/bold]")
                print(f"[dim]{command["desc"]}[/dim]")
                print("\n[bold]📦 Arguments:[/bold]")
                print(f"[white]{json.dumps(command['args'], indent=2, ensure_ascii=False)}[/white]")

                userConfirm = Prompt.ask("Are you OK", default="y", choices=["y", "n"])

                if userConfirm == "y":
                    result = command["action"](**command["args"])
                    chatHistory.append({"role": "system", "content": f"AgentCode Session ID {current_session_id} EXECUTED '{command["id"]}'. \nResult: '''{repr(result)}'''"})
                    main(modelID)
                else:
                    raise RuntimeError("Sorry, the user refused to run.")
            
            except Exception as e:
                chatHistory.append({"role": "system", "content": f"AgentCode Session ID {current_session_id} EXECUTED '{command["id"]}'\nError: '''{e}'''"})
    else:
        print(response)

if __name__ == "__main__":
    modelID = Prompt.ask("OpenAI Model ID", default="gpt-4o-mini")
    kit.setDefaults()
    for command in exampleAvailableCommands:
        kit.addCommand(id=command["id"], args=command["args"], desc=command["desc"], action=command["action"])
    while True:
        prompt = input(">>> ")
        chatHistory.append({"role": "user", "content": prompt})
        main(modelID)
