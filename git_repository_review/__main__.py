"""Blueprint for a quick start of a new Python project."""

import sys

from git_repository_review.validate import main

if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
