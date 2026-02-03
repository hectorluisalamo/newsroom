# ABOUTME: Entry point for `python -m newsroom` invocation.
# ABOUTME: Loads environment variables and delegates to the CLI parser.
"""Entry point for running newsroom as a module."""

from dotenv import load_dotenv

from newsroom.cli import main

if __name__ == "__main__":
    load_dotenv()
    main()
