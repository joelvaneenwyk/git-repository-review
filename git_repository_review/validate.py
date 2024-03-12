"""This script reads the .gitattributes file line by line. For each line, it
uses a regular expression to match lines that start with an asterisk followed
by a file extension, a space, and then a command. It then adds the extension
and command to a dictionary. If an extension is already in the dictionary, it
appends the new command to the existing list of commands for that extension. It
also walks through a directory and maps file extensions to the files that have
them. It then prints the extension-command mappings and the extension-file
mappings.
"""

import os
import re
import subprocess
from collections import defaultdict

from pathspec.gitignore import GitIgnoreSpec


def parse_gitattributes(file_path) -> dict[str, list[str]]:
    """This script reads the .gitattributes file line by line. For each line, it uses a regular expression to match lines that start with an asterisk followed by a file extension, a space, and then a command. It then adds the extension and command to a dictionary. If an extension is already in the dictionary, it appends the new command to the existing list of commands for that extension."""
    with open(file_path) as file:
        lines = file.readlines()

    # Regular expression to match lines like "*.extension command"
    pattern: re.Pattern[str] = re.compile(r"\*(\.\w+)\s+(.+)")

    # Dictionary to hold extension-command mappings
    extension_commands: dict[str, list[str]] = defaultdict(list)

    for line in lines:
        match = pattern.match(line.strip())
        if match:
            extension = str(match.group(1))
            commands = str(match.group(2)).split(" ")
            extension_commands[extension] = commands

    return extension_commands


def map_extensions_to_files(directory) -> dict[str, list[str]]:
    # Dictionary to hold extension-file mappings
    extension_files: dict[str, list[str]] = defaultdict(list)

    # Walk through directory
    for root, _, files in os.walk(directory):
        for file in files:
            # Get file extension
            remainder, extension = os.path.splitext(file)
            ext = str(extension if extension else remainder)
            # Add file to the list of files with the same extension
            relative_root = str(
                os.path.join(root, file)
                .replace(directory, "")
                .replace("\\", "/")
                .lstrip("/")
            )
            extension_files[ext].append(relative_root)

    return extension_files


def git_rm(file_path):
    # Run the git rm command
    result = subprocess.run(
        ["git", "rm", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Check if the command was successful
    if result.returncode != 0:
        # throw an error if the command was not successful
        raise Exception(f"Error: {result.stderr.decode()}")

    print(f"Successfully removed file: {file_path}")


def run(root_directory: str | None = None) -> int:
    # Use the function
    directory = os.path.abspath(
        root_directory or "."
    )  # Replace with your project directory
    attrs = parse_gitattributes(".gitattributes")
    files = map_extensions_to_files(directory)

    ignore_file = os.path.join(directory, ".gitignore")

    # Run the git ls-files command and get the output
    result = subprocess.run(
        ["git", "ls-files", directory],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # If the file is in the output, it is committed
    committed_files_data = result.stdout.decode()
    committed_files = []
    for filepath in committed_files_data.splitlines():
        committed_files.append(filepath)

    with open(ignore_file) as file:
        gitignore = file.read()

    # Create a pathspec using the .gitignore file
    spec = GitIgnoreSpec.from_lines(gitignore.splitlines())

    unmatched: list[str] = []
    for item in files:
        instances = files[item]
        for instance in instances:
            if instance in committed_files and spec.match_file(instance):
                git_rm(instance)

        if item and item not in attrs:
            unmatched.append(item)

    print(unmatched)

    return len(unmatched)
