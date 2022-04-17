#!/usr/bin/env python3
import re
import subprocess


def run_command(cmd):
    return subprocess.run(['bash', '-c', cmd], capture_output=True, check=True).stdout.decode("utf-8").strip("\n")


output = ''
with open('README.md', 'r', encoding='utf-8') as file_handler:
    is_between_placeholders = False
    for line in file_handler:

        matches = re.match(r'\[\/\/\]\: \<\> \(command-placeholder-start "(.*)"\)', line)
        if not is_between_placeholders and matches is not None:
            is_between_placeholders = True
            output += line
            output += "```\n%s\n```\n" % (run_command(matches.group(1)))
            continue

        matches = re.match(r'\[\/\/\]\: \<\> \(command-placeholder-end\)', line)
        if is_between_placeholders and matches is not None:
            is_between_placeholders = False
            output += line
            continue
        if not is_between_placeholders:
            output += line

with open('README.md', 'w', encoding='utf-8') as file_handler:
    file_handler.write(output)
