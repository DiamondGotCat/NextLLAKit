#!/usr/bin/env python

# NextLLAKit: NextLLA for Custom Script (Python)
# Copyright (c) 2025 DiamondGotCat
# MIT License

import uuid

class NextLLAKit():

    def __init__(self):
        self.var = {}
        self.var["systemPrompt"] = ""
        self.var["currentSessionID"] = uuid.uuid4()
        self.var["availableCommands"] = []

    def main_process(self, input, autoUpdateSession=True):

        isContainCommand = False
        containCommands = []

        commands_result = self._parseAgentCode(input)
        commands = commands_result["data"]
        available_commands_by_id = {cmd["id"]: cmd for cmd in self.getVar("availableCommands")["data"]}
        
        if 0 < len(commands):
            isContainCommand = True
            for command in commands:
                cmd_id = command["id"]
                if cmd_id in available_commands_by_id:
                    action_func = available_commands_by_id[cmd_id]["action"]
                    containCommands.append({"id": cmd_id, "desc": available_commands_by_id[cmd_id]['desc'].strip(), "args": command['args'], "action": action_func})

        output = {"status": "success", "data": {"sessionID": self.getVar("availableCommands")["data"], "isContainCommand": isContainCommand, "containCommands": containCommands}}
        if autoUpdateSession:
            self.updateSession()
        return output

    def getSystemPrompt(self):
        a = self.var["systemPrompt"]
        for key in self.var.keys:
            a.replace("{" + key + "}", self.var[key])
        return a

    def getVar(self, id):
        return {"status": "success", "data": self.var[id]}

    def setVar(self, id, content):
        self.var[id] = content
        return {"status": "success", "data": None}
        
    def updateSession(self):
        self.var["currentSessionID"] = uuid.uuid4()

    def _parseAgentCode(self, response):
        lines = response.splitlines()
        in_block = False
        commands = []
        current_command = None
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            if line == "!AgentCode start":
                in_block = True
                i += 1
                continue
            if line == "!AgentCode end":
                in_block = False
                i += 1
                continue
            if in_block:
                if line.startswith("!") and not line.startswith("!!"):
                    if current_command:
                        commands.append(current_command)
                    command_id = line[1:].strip()
                    current_command = {"id": command_id, "args": {}}
                    i += 1
                    continue
                elif line.startswith("!!"):
                    if current_command is None:
                        i += 1
                        continue
                    header = line[2:]
                    if ":" not in header:
                        i += 1
                        continue
                    header_parts = header.split(":", 1)
                    cmd_id = header_parts[0].strip()
                    arg_name = header_parts[1].strip()
                    arg_lines = []
                    i += 1
                    while i < len(lines) and lines[i].strip() != "!!":
                        arg_lines.append(lines[i])
                        i += 1
                    i += 1
                    arg_value = "\n".join(arg_lines).strip()
                    current_command["args"][arg_name] = arg_value
                    continue
                else:
                    i += 1
                    continue
            else:
                i += 1
        if current_command:
            commands.append(current_command)
        return {"status": "success", "data": commands}

    def addCommand(self, id, args, desc, action):
        self.var["availableCommands"].append({"id": id, "args": args, "desc": desc, "action": action})
        return {"status": "success", "data": None}

    def removeCommand(self, id):
        self.var["availableCommands"].remove(id)

    def setDefaults(self):
        self.var["systemPrompt"] = """
You are an excellent assistant.
Your name is "NextLLA".
You can use AgentCode to access various functionalities.

# About AgentCode

Using AgentCode is simple.  
All you have to do is say something like the following in your response:

```
!AgentCode start
!runPython  
!!runPython:content  
result1 = len("Hello, World!")  
!!  
!!runPython:resultVar  
result1  
!!  
!AgentCode end  
```

```
!AgentCode start
!runShellCommand  
!!runShellCommand:command  
echo 1 + 1
!!
!AgentCode end  
```

- `!AgentCode start`: Start AgentCode
- `!<commandName>`: Set AgentCode Command for Execute
- `!!<commandName>:<argID>`: Set argID for following Content
- `!!`: End of that Arg.
- `!AgentCode end`: End AgentCode

After saying this, you should end your response.  
Once your response ends, the system (role) will report the result back to you.  

Below is a list of available AgentCode commands:

```
{availableCommands}
```

Current Session ID: {currentSessionID}
        """
