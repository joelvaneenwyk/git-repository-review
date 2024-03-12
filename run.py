"""Validate the contents of a given Git repository.

Read the '.gitattributes' file line by line and for each line, it
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
import sys
from collections import defaultdict

from dotenv import load_dotenv
from pathspec.gitignore import GitIgnoreSpec


def parse_gitattributes(file_path) -> dict[str, list[str]]:
    """Read the .gitattributes file line by line.

    For each line, it uses a regular expression to match lines that start with
    an asterisk followed by a file extension, a space, and then a command. It
    then adds the extension and command to a dictionary. If an extension is
    already in the dictionary, it appends the new command to the existing
    list of commands for that extension.
    """
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


def git_rm(repository, file_path):
    # Run the git rm command
    result = subprocess.run(
        ["git", "-C", repository, "rm", file_path],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # Check if the command was successful
    if result.returncode != 0:
        # throw an error if the command was not successful
        raise Exception(f"Error: {result.stderr.decode()}")

    print(f"Successfully removed file: {file_path}")


def main(root: str | None = None) -> int:
    load_dotenv()

    directory = os.path.abspath(root or os.getenv("FILE_PATH") or ".")
    print(directory)

    gitignore = os.path.join(directory, ".gitignore")
    gitattributes = os.path.join(directory, ".gitattributes")
    git_attributes_mapping = parse_gitattributes(gitattributes)
    file_extensions_mapping = map_extensions_to_files(directory)

    # Run the git ls-files command and get the output
    result = subprocess.run(
        ["git", "-C", directory, "ls-files"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )

    # If the file is in the output, it is committed
    committed_files_data = result.stdout.decode()
    committed_files = []
    for filepath in committed_files_data.splitlines():
        committed_files.append(filepath)

    with open(gitignore) as file:
        gitignore = file.read()

    # Create a pathspec using the .gitignore file
    spec = GitIgnoreSpec.from_lines(gitignore.splitlines())

    unmatched: list[str] = []
    for item in file_extensions_mapping:
        instances = file_extensions_mapping[item]
        for instance in instances:
            if instance in committed_files and spec.match_file(instance):
                git_rm(directory, instance)

        if item and item not in git_attributes_mapping:
            unmatched.append(item)

    print(unmatched)

    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
