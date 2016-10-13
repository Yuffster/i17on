#!/usr/bin/env python

import sys
import copy
from i17on import translator


def main(stdout=None, argv=None):
    """
    Uses sys to grab the command-line args and normalizes them for
    execution.
    """
    stdout = stdout or sys.stdout
    argv = argv or sys.argv

    argv = copy.copy(sys.argv)  # We're gonna mutate this.
    argv.pop(0)  # Name of the script; don't need it.

    # stdin is like `foo.txt | i17on`
    # or `i17on < foo.txt`
    if not sys.stdin.isatty():
        text = sys.stdin.read()
    else:
        # If no data is piped in, the first argument is the filename.
        fname = argv.pop(0)
        with open(fname,'r') as f: text = f.read()
    
    stdout.write(execute(text, argv))


def execute(text, argv=None):
    """
    Takes normalized args and runs them through the translator.

    Text is the input (can come from a filename or from stdin), 
    argv is just a list of all the command-line arguments besides
    the input.

    Any arbitrary argument will be a tag, unless it's prepended by
    --, in which case it will be a flag.  No verification is done
    on invalid tags.

    Valid Tags:

        --debug: print the AST and brace matching

    If the flags get more complicated, I'll write a more sophisticated
    argument parser.
    """
    argv = argv or []

    # Grab the other args.
    flags = []
    tags = []
    for arg in argv:
        if arg[0:2] == '--':
            flags.append(arg[2:])
        else:
            tags.append(arg)

    if 'debug' in flags:
        translator.debug_all = True

    return translator.translate(text, tags)


if __name__ == "__main__":
    main()
