#!/usr/bin/env python

"""
A server that provides a graphical user interface to the gnu debugger (gdb).
https://github.com/cs01/gdbgui
"""

import argparse
import json
import logging
import os
import platform
import re
import shlex
import sys



def get_parser():
    parser = argparse.ArgumentParser(description=__doc__)

    gdb_group = parser.add_argument_group(title="gdb settings")
    args_group = parser.add_mutually_exclusive_group()
    network = parser.add_argument_group(title="gdbgui network settings")
    security = parser.add_argument_group(title="security settings")
    other = parser.add_argument_group(title="other settings")

    gdb_group.add_argument(
        "-g",
        "--gdb",
        help="Path to debugger. Default: ",
        default="",
    )
    gdb_group.add_argument(
        "--gdb-args",
        help=(
            "Arguments passed directly to gdb when gdb is invoked. "
            'For example,--gdb-args="--nx --tty=/dev/ttys002"'
        ),
        default="",
    )
    gdb_group.add_argument(
        "--rr",
        action="store_true",
        help=(
            "Use `rr replay` instead of gdb. Replays last recording by default. "
            "Replay arbitrary recording by passing recorded directory as an argument. "
            "i.e. gdbgui /recorded/dir --rr. See http://rr-project.org/."
        ),
    )
    network.add_argument(
        "-p",
        "--port",
        help="The port on which gdbgui will be hosted. Default: ",
        default="",
    )
    network.add_argument(
        "--host",
        help="The host ip address on which gdbgui serve. Default: ",
        default="",
    )
    network.add_argument(
        "-r",
        "--remote",
        help="Shortcut to set host to 0.0.0.0 and suppress browser from opening. This allows remote access "
        "to gdbgui and is useful when running on a remote machine that you want to view/debug from your local "
        "browser, or let someone else debug your application remotely.",
        action="store_true",
    )

    security.add_argument(
        "--auth-file",
        help="Require authentication before accessing gdbgui in the browser. "
        "Specify a file that contains the HTTP Basic auth username and password separate by newline. ",
    )

    security.add_argument("--user", help="Username when authenticating")
    security.add_argument("--password", help="Password when authenticating")
    security.add_argument(
        "--key",
        default=None,
        help="SSL private key. "
        "Generate with:"
        "openssl req -newkey rsa:2048 -nodes -keyout host.key -x509 -days 365 -out host.cert",
    )
    # https://www.digitalocean.com/community/tutorials/openssl-essentials-working-with-ssl-certificates-private-keys-and-csrs
    security.add_argument(
        "--cert",
        default=None,
        help="SSL certificate. "
        "Generate with:"
        "openssl req -newkey rsa:2048 -nodes -keyout host.key -x509 -days 365 -out host.cert",
    )
    # https://www.digitalocean.com/community/tutorials/openssl-essentials-working-with-ssl-certificates-private-keys-and-csrs

    other.add_argument(
        "--remap-sources",
        "-m",
        help=(
            "Replace compile-time source paths to local source paths. "
            "Pass valid JSON key/value pairs."
            'i.e. --remap-sources=\'{"/buildmachine": "/home/chad"}\''
        ),
    )
    other.add_argument(
        "--project",
        help='Set the project directory. When viewing the "folders" pane, paths are shown relative to this directory.',
    )
    other.add_argument("-v", "--version", help="Print version", action="store_true")

    other.add_argument(
        "--hide-gdbgui-upgrades",
        help=argparse.SUPPRESS,  # deprecated. left so calls to gdbgui don't break
        action="store_true",
    )
    other.add_argument(
        "-n",
        "--no-browser",
        help="By default, the browser will open with gdbgui. Pass this flag so the browser does not open.",
        action="store_true",
    )
    other.add_argument(
        "-b",
        "--browser",
        help="Use the given browser executable instead of the system default.",
        default=None,
    )
    other.add_argument(
        "--debug",
        help="The debug flag of this Flask application. "
        "Pass this flag when debugging gdbgui itself to automatically reload the server when changes are detected",
        action="store_true",
    )

    args_group.add_argument(
        "cmd",
        nargs="?",
        type=lambda prog: [prog],
        help="The executable file and any arguments to pass to it."
        " To pass flags to the binary, wrap in quotes, or use --args instead."
        " Example: gdbgui ./mybinary [other-gdbgui-args...]"
        " Example: gdbgui './mybinary myarg -flag1 -flag2' [other gdbgui args...]",
        default=[],
    )
    args_group.add_argument(
        "--args",
        nargs=argparse.REMAINDER,
        help="Specify the executable file and any arguments to pass to it. All arguments are"
        " taken literally, so if used, this must be the last argument"
        " passed to gdbgui."
        " Example: gdbgui [...] --args ./mybinary myarg -flag1 -flag2",
        default=[],
    )
    return parser


def main():
    """Entry point from command line"""
    parser = get_parser()
    args = parser.parse_args()

    print(args.remap_sources)
    d = json.loads(args.remap_sources)
    print(d)



if __name__ == "__main__":
    main()
