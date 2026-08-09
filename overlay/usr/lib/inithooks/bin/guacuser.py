#!/usr/bin/env python3
# Copyright (c) 2026 Mike Benson <mike@kambe.com.au> - all rights reserved

"""
Configure Guacamole user in MySQL/MariaDB

Options:
    -u --user= <username>   guacamole username. If not provided will ask interactively
    -p --pass= <password>   guacamole local password. If not provided, will ask interactively
    -H --host= hostname     optional (default: localhost). Never asked interactively.

"""

import argparse
import signal
import sys
import time
from contextlib import contextmanager
from itertools import chain
from os import system
from textwrap import wrap

import pymysql
import pymysql.cursors
from libinithooks.dialog_wrapper import Dialog, password_complexity

DEBIAN_CNF = "/etc/mysql/debian.cnf"


class Error(Exception):
    pass


class MySQL:
    def __init__(self):
        system("mkdir -p /var/run/mysqld")
        system("chown mysql:root /var/run/mysqld")

        self.selfstarted = False
        self.connected = False

    def __enter__(self):
        if not self._is_alive():
            system("mysqld --skip-networking >/dev/null 2>&1 &")
            for i in range(6):
                if self._is_alive():
                    break
                time.sleep(1)
            else:
                raise Error("could not start mysqld")
            self.selfstarted = True
        return self

    def __exit__(self, *_):
        if self.connected:
            self.connection.commit()
            self.connection.close()
        if self.selfstarted:
            system(f"mysqladmin --defaults-file={DEBIAN_CNF} shutdown")

    @contextmanager
    def _cursor(self):
        if not self.connected:
            self.connection = pymysql.connect(
                unix_socket="/run/mysqld/mysqld.sock",
                user="root",
                database="guacamole_db",
                cursorclass=pymysql.cursors.Cursor,
            )
            self.connected = True
        yield self.connection.cursor()

    def _is_alive(self):
        return system("mysqladmin -s ping >/dev/null 2>&1") == 0

    def execute(self, query, interp=None, output=False):
        with self._cursor() as cursor:
            cursor.execute(query, interp)
            if output:
                return cursor.fetchall()


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description="Create a new user in the Apache Guacamole Database"
    )
    _ = parser.add_argument(
        "-u",
        "--user",
        dest="username",
        default="",
        help="Guacamole username. If not set will be asked interactively.",
    )
    _ = parser.add_argument(
        "-p",
        "--pass",
        dest="password",
        const="\127",
        help="Optional internal password. Specify this option with no "
        "password to set the password interactively. Omit this option to "
        "require the user to be authenticated by some external mechanism "
        "(eg LDAP or OIDC)",
        nargs="?",
    )
    args = parser.parse_args(argv)
    if not args.username and args.password:
        parser.error(
            "A password can only be set if an explicit username is given"
        )
        sys.exit(1)

    return args


def conduct_dialog(args):
    d = Dialog("TurnKey Linux - First boot configuration")
    #    d.console.add_persistent_args(["--trace", "/var/log/dialog.log"])
    tags = (getattr(args, "username", ""), "", "")
    ro = 2 if tags[0] else 0
    width = d.width - 2

    while True:
        elements = []
        pos = 1
        secure = ro

        labels = ("Username:", "Password:", "Confirm password:")
        lwidth = max(len(l) for l in labels) + 2
        for pos, (label, tag) in enumerate(zip(labels, tags), start=1):
            elements.append(
                [label, pos, 1, tag, pos, lwidth, width - lwidth, 256, secure]
            )
            secure = 1

        text = (
            "If the user is internal, specify and confirm a password.\n\n"
            "Otherwise, leave the password fields blank if the user can be "
            "authenticated externally (LDAP or OIDC)."
        )
        # This ensures the text fits the window width, but newlines are preserved.
        textlines = list(
            chain.from_iterable(
                wrap(l, width=width - 2) if len(l) else [""]
                for l in text.split("\n")
            )
        )
        preamble = len(textlines) + 7

        code, tags = d.wrapper(
            "mixedform",
            "\n".join(textlines),
            elements,
            height=d.height,
            width=d.width,
            form_height=min(d.height - preamble, len(labels)),
            title="Create a Guacamole user",
            ok_label="Ok",
            no_cancel="True",
            insecure=True,
        )
        if code != d.console.OK:
            continue
        else:
            if not tags[0]:
                d.error("Please supply a username.")

            if not tags[1]:
                break

            if not tags[2] or (tags[1] != tags[2]):
                d.error("Password mismatch, please try again.")
                ro = 2
                tags = (tags[0], "", "")
                continue

            if password_complexity(tags[1]) < 3:
                d.error(
                    "Insecure password! Mix uppercase, lowercase,"
                    " and at lease one number. Multiple words and"
                    " punctuation are highly recommended but not"
                    " strictly required"
                )
                ro = 2
                tags = (tags[0], "", "")
                continue

            args.username = tags[0]
            args.password = tags[1]
            break

    return args


def create_internal_user(values):
    with MySQL() as m:
        # Create base entity entry for user if it doesn't already exist
        m.execute(
            "INSERT IGNORE INTO guacamole_entity (name, type) "
            "VALUES (%(username)s, 'USER');",
            interp=values,
        )

        # Insert or update the user with the password that has been set
        # We use successive queries, because pymysql can't seem to cope with
        # queries containing multiple statements

        # create the  salt
        m.execute("SET @salt = UNHEX(SHA2(UUID(), 256));")

        # Insert or Update the user with an internal password
        m.execute(
            """
	    -- Create or Update user with password hashed with the salt
	    INSERT INTO guacamole_user (
	        entity_id,
	        password_salt,
	        password_hash,
	        password_date
	    )
	    SELECT
	        entity_id,
	        @salt,
                UNHEX(SHA2(CONCAT(%(password)s, HEX(@salt)), 256)),
	        CURRENT_TIMESTAMP
	    FROM guacamole_entity
	    WHERE
	        name = %(username)s
	        AND type = 'USER'
            ON DUPLICATE KEY UPDATE 
                password_salt = @salt,
                password_hash = UNHEX(SHA2(CONCAT(%(password)s, HEX(@salt)), 256)),
                password_date = CURRENT_TIMESTAMP
            ;
            """,
            interp=values,
        )


def create_external_user(values):
    with MySQL() as m:
        # Create base entity entry for user if it doesn't already exist
        m.execute(
            "INSERT IGNORE INTO guacamole_entity (name, type) "
            "VALUES (%(username)s, 'USER');",
            interp=values,
        )

        # Insert or Update the user with no password
        # This assumes the user will be authenticated by some other method
        m.execute(
            """
    	    INSERT INTO guacamole_user (
	        entity_id,
	        password_salt,
	        password_hash,
	        password_date
            )
    	    SELECT
	        entity_id,
                NULL,
                0,
                CURRENT_TIMESTAMP
	    FROM guacamole_entity
	    WHERE
	        name = %(username)s
	        AND type = 'USER'
            ON DUPLICATE KEY UPDATE
                password_salt = NULL,
                password_hash = 0,
                password_date = CURRENT_TIMESTAMP
            ;
        """,
            interp=values,
        )


def main(argv):
    signal.signal(signal.SIGINT, signal.SIG_IGN)

    args = parse_args(argv)

    values = vars(
        conduct_dialog(args)
        if not args.username or args.password == "\127"
        else args
    )

    if args.password:
        create_internal_user(values)
    else:
        create_external_user(values)

    sys.exit(0)


if __name__ == "__main__":
    main(sys.argv[1:])
