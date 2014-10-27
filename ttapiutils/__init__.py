"""
usage: ttapiutils [--help] [options] <command> [<args>...]

options:
    -h, --help  Show this help message

Available commands:
{commands}
"""
from __future__ import print_function

import sys

import docopt
import pkg_resources


def get_subcommand_entrypoints():
    return dict(
        (ep.name, ep) for ep in
        pkg_resources.iter_entry_points(
            group="ttapiutils_subcommands"))


def format_command_names(subcommands):
    names = sorted(name for name in subcommands.keys())
    return "\n".join("    {}".format(name) for name in names)


def run_command(entrypoint, args):
    loaded = entrypoint.load()
    loaded.main(args)


def main():
    subcommands = get_subcommand_entrypoints()
    doc = __doc__.format(commands=format_command_names(subcommands))
    args = docopt.docopt(doc, options_first=True)

    cmd_name = args["<command>"]
    if cmd_name not in subcommands:
        print("ttapiutils: {!r} is not a ttapiutils command. "
              "See ttapiutils --help.".format(cmd_name),
              file=sys.stderr)
        sys.exit(1)

    # Pass arguments after <command> through to subcommand...
    run_command(subcommands[cmd_name], [cmd_name] + args["<args>"])


if __name__ == "__main__":
    main()
