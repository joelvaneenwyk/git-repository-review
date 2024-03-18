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

import logging
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
    with open(file_path, encoding="utf-8") as file:
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


def map_extensions_to_files(directory: str) -> dict[str, list[str]]:
    """Given directory, return mapping of file extensions to files with that extension."""
    # Dictionary to hold extension-file mappings
    extension_files: dict[str, list[str]] = defaultdict(list)

    # Walk through directory
    for root, _, files in os.walk(directory):
        for filename in files:
            # Get file extension
            remainder, extension = os.path.splitext(filename)
            ext = str(extension if extension else remainder)
            # Add file to the list of files with the same extension
            relative_root = str(os.path.join(root, filename).replace(directory, "").replace("\\", "/").lstrip("/"))
            extension_files[ext].append(relative_root)

    return extension_files


def git_rm(repository: str, file_path: str) -> str:
    """Run the git rm command."""
    result = git("-C", repository, "rm", file_path)

    print(f"Successfully removed file: {file_path}")

    return result.stdout.decode()


def find_executable(executable: str, path: str | None = None) -> str | None:
    """Find if 'executable' can be run.

    Looks for it in 'path' (string that lists directories separated by
    'os.pathsep'; defaults to os.environ['PATH']). Checks for all executable
    extensions. Returns full path or None if no command is found.
    """
    path_environment: str = path or os.environ.get("PATH") or ""
    paths = path_environment.split(os.pathsep)
    extlist = [""]
    if os.name == "os2":
        (_, ext) = os.path.splitext(executable)
        # executable files on OS/2 can have an arbitrary extension, but
        # .exe is automatically appended if no dot is present in the name
        if not ext:
            executable = executable + ".exe"
    elif sys.platform == "win32":
        pathext = os.environ["PATHEXT"].lower().split(os.pathsep)
        (_, ext) = os.path.splitext(executable)
        if ext.lower() not in pathext:
            extlist = pathext
        # Windows looks for binaries in current dir first
        paths.insert(0, "")

    for ext in extlist:
        execname = executable + ext
        for p in paths:
            f = os.path.join(p, execname)
            if os.path.isfile(f):
                return f

    return None


def git(*args: str) -> subprocess.CompletedProcess[bytes]:
    """Run the git command."""
    git_executable = find_executable("git")
    if git_executable is None:
        raise FileNotFoundError("git not found")

    arguments = list(args)
    result = subprocess.run([git_executable] + arguments, capture_output=True, check=True)

    # Check if the command was successful
    if result.returncode != 0:
        # throw an error if the command was not successful
        raise ChildProcessError(f"Error: {result.stderr.decode()}")

    return result


def main(root: str | None = None) -> int:
    """Review the contents of a given Git repository."""
    load_dotenv()

    logging.basicConfig(level=logging.DEBUG)
    logger = logging.getLogger(__name__)

    directory = os.path.abspath(root or os.getenv("FILE_PATH") or ".")
    if not os.path.isdir(directory):
        logger.error("Directory does not exist: '%s'", directory)
        return 2

    logger.info("Directory: '%s'", directory)

    gitignore = os.path.join(directory, ".gitignore")
    gitattributes = os.path.join(directory, ".gitattributes")
    git_attributes_mapping = parse_gitattributes(gitattributes)
    file_extensions_mapping = map_extensions_to_files(directory)

    # Run the git ls-files command and get the output
    result = git("-C", directory, "ls-files")

    # If the file is in the output, it is committed
    committed_files_data = result.stdout.decode()
    committed_files = []
    for filepath in committed_files_data.splitlines():
        committed_files.append(filepath)

    with open(gitignore, encoding="utf-8") as file:
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

    logger.info("Unmatched: '%s'", unmatched)

    return 0
