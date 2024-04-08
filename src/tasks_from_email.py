#!/usr/bin/python3.6
################################################################################
# tasks_from_email.py - Create kanboard tasks from email
################################################################################
#
# Copyright (C) $( 2020 ) Radio Bern RaBe
#                    Switzerland
#                    http://www.rabe.ch
#
# This program is free software: you can redistribute it and/or
# modify it under the terms of the GNU Affero General Public
# License as published  by the Free Software Foundation, version
# 3 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public
# License  along with this program.
# If not, see <http://www.gnu.org/licenses/>.
#
# Please submit enhancements, bugfixes or comments via:
# https://github.com/radiorabe/kanboard-tasks-from-email
#
# Authors:
#  Simon Nussbaum <smirta@gmx.net>
#
# Description:
# Create tasks by fetching unread emails from a mailbox.
#
# Usage:
# python3 tasks_from_email.py
#


"""Import libraries and config file."""

from __future__ import annotations

import base64
import datetime
import email
import imaplib
import re
import time
from pathlib import Path
from textwrap import dedent
from typing import TYPE_CHECKING, Any, NoReturn

import kanboard  # type: ignore[import-untyped]
from configargparse import ArgumentParser  # type: ignore[import-untyped]

if TYPE_CHECKING:  # pragma: no cover
    from argparse import Namespace


def get_arguments(parser: ArgumentParser) -> Namespace:
    """Configure argument parsing.

    Arguments:
    ---------
        parser: the parser to add arguments

    Returns:
    -------
        args: the parsed args from the parser

    """
    for arg in [
        # mail server
        (
            "--imaps-server",
            {"dest": "IMAPS_SERVER", "help": "fqdn of mail sever", "required": True},
        ),
        (
            "--imaps-user",
            {
                "dest": "IMAPS_USERNAME",
                "env_var": "IMAPS_USERNAME",
                "help": "imap user name",
                "required": True,
            },
        ),
        (
            "--imaps-password",
            {
                "dest": "IMAPS_PASSWORD",
                "env_var": "IMAPS_PASSWORD",
                "help": "imap user password",
                "required": True,
            },
        ),
        # kanboard
        (
            "--kanboard-connect-url",
            {
                "dest": "KANBOARD_CONNECT_URL",
                "help": "url for API requests",
                "required": True,
            },
        ),
        (
            "--kanboard-api-token",
            {
                "dest": "KANBOARD_API_TOKEN",
                "help": "API token from a user that is allowed to create tasks",
                "required": True,
            },
        ),
        (
            "--kanboard-project-name",
            {
                "dest": "KANBOARD_PROJECT_NAME",
                "help": "Name of the kanboard project where tasks are to be created.",
                "default": "Support",
            },
        ),
        (
            "--kanboard-due-offset-hours",
            {
                "dest": "KANBOARD_TASK_DUE_OFFSET_IN_HOURS",
                "help": "Number of hours the task is due after mail received",
                "default": 48,
            },
        ),
        (
            "--kanboard-group-id",
            {
                "dest": "KANBOARD_GROUP_ID",
                "help": (
                    "ID of group new users shall be added to. "
                    "If set to 0 (default), the new user won't be added to a group."
                ),
                "default": 0,
            },
        ),
        # various
        (
            "--well-known-email-addresses",
            {
                "dest": "WELL_KNOWN_EMAIL_ADDRESSES",
                "help": (
                    "well-known mail addresses from where emails could be forwarded"
                    "because they were sent to the wrong address"
                ),
                "default": [],
            },
        ),
    ]:
        name, params = arg
        params["env_var"] = params["dest"]
        parser.add_argument(name, **params)

    return parser.parse_args()


def convert_to_kb_date(date_str: str, increment_by_hours: int = 0) -> str:
    """Convert date into a kanboard compatible date.

    Arguments:
    ---------
        date_str: String containing a date from an email (tested with emails only)
        increment_by_hours: Number of hours offset to date_str

    Returns:
    -------
        the date in kanboard compatible format %d.%m.%Y %H:%M

    """
    local_kb_date = None
    date_tuple = email.utils.parsedate(date_str)
    # add 12 hours if the passed date string is in 12-hours format
    # and it ends with 'PM'
    if date_str[-2:] == "PM":
        increment_by_hours += 12
    if date_tuple:
        local_timezone = (
            datetime.datetime.now(datetime.timezone(datetime.timedelta(0)))
            .astimezone()
            .tzinfo
        )
        local_date = datetime.datetime.fromtimestamp(
            time.mktime(date_tuple), local_timezone
        )
        if increment_by_hours > 0:
            local_date = local_date + datetime.timedelta(hours=increment_by_hours)
        local_kb_date = "%s" % (str(local_date.strftime("%d.%m.%Y %H:%M")))
    return local_kb_date


def imap_connect(server: str, user: str, password: str) -> imaplib.IMAP4_SSL:
    """Connect and authenticate against mailserver."""
    imap_connection = imaplib.IMAP4_SSL(server)
    imap_connection.login(user, password)
    return imap_connection


def imap_close(imap_connection: imaplib.IMAP4_SSL) -> NoReturn:
    """Close mailserver connection."""
    imap_connection.close()
    imap_connection.logout()


def imap_search_unseen(imap_connection: imaplib.IMAP4_SSL) -> imaplib._CommandResults:
    """Get unread mails."""
    imap_connection.select("INBOX")
    return imap_connection.search(None, "unseen")


def walk_message_parts(email_message: email.message.EmailMessage) -> tuple[str, dict]:
    """Grab the body and all named attachments from a message."""
    body = None
    kb_attachments = {}

    for part in email_message.walk():
        """ get plain text body details """
        if part.get_content_maintype() == "multipart":
            continue
        if part.get("Content-Disposition") is None:
            if part.get_content_type() == "text/plain":
                body = re.sub(
                    "\r\n", "\r\n\r\n", part.get_payload(decode=True).decode("utf-8")
                )
            continue
        file_name = email.header.make_header(
            email.header.decode_header(part.get_filename())
        )
        if bool(file_name):
            kb_attachments[str(file_name)] = base64.b64encode(
                part.get_payload(decode=True)
            )
            body = f"{body}\n\n<< Attachment: {file_name} >>"
    return (body, kb_attachments)


def handle_well_known_forwarders(  # noqa: PLR0913
    well_known: list[str],
    offset: int,
    body: str,
    email_address: str,
    local_task_start_date_iso8601: str,
    local_task_due_date_iso8601: str,
) -> tuple:
    """Handle known addresses.

    If the email has been forwarded from specified addresses use sender
    email address and timestamp from message body.
    """
    fwd_email_addresses = re.findall("(From:.*\S+@\S+|To:.*\S+@\S+)", "%s" % body)
    if fwd_email_addresses:
        fwd_to_email_address = re.sub(
            "[<>]", "", re.findall("\S+@\S+", fwd_email_addresses[1])[-1]
        )
        if fwd_to_email_address in well_known:
            email_address = re.sub(
                "[<>]", "", re.findall("\S+@\S+", fwd_email_addresses[0])[-1]
            )
            local_task_start_date_iso8601 = convert_to_kb_date(
                re.sub(
                    "Date:\s*",
                    "",
                    re.search("Date:[\S ]+", "%s" % body, re.MULTILINE).group(0),
                )
            )
            local_task_due_date_iso8601 = convert_to_kb_date(
                re.sub(
                    "Date:\s*",
                    "",
                    re.search("Date:[\S ]+", "%s" % body, re.MULTILINE).group(0),
                ),
                offset,
            )
    return email_address, local_task_start_date_iso8601, local_task_due_date_iso8601


def create_user_for_sender(
    kb: kanboard.Client,
    email_address: str,
) -> int:
    """Create user for sender email if it doesn't exist."""
    kb_user_id = None
    kb_users = kb.get_all_users()
    for kb_user in kb_users:
        if kb_user["email"] == email_address:
            kb_user_id = kb_user["id"]
    if kb_user_id is None:
        kb_user_id = kb.create_user(
            username=email_address, password=email_address, email=email_address
        )
    return kb_user_id


def get_task_if_subject_matches(
    kb: kanboard.Client,
    subject: str,
) -> tuple[int, Any]:
    """Search for link to already existing task."""
    kb_task_id = False
    kb_task = None
    kb_task_search_result = re.findall("\[KB#\d+", "%s" % subject)
    if kb_task_search_result:
        kb_task_id = re.sub("\[KB#", "", kb_task_search_result[-1])
        """ test if task already exists """
        kb_task = kb.get_task(task_id=kb_task_id)
    return kb_task_id, kb_task


def reopen_and_update(  # noqa: PLR0913
    kb: kanboard.Client,
    kb_task: dict,
    kb_task_id: int,
    kb_user_id: int,
    kb_text: str,
    local_task_due_date_iso8601: str,
) -> NoReturn:
    """Reopen task, update due date and add email as comment."""
    if kb_task["is_active"] == 0:
        kb.open_task(task_id=kb_task_id)
    """ add email as comment """
    kb.create_comment(task_id=kb_task_id, user_id=kb_user_id, content=kb_text)
    kb.update_task(id=kb_task_id, date_due=local_task_due_date_iso8601)


def main() -> NoReturn:
    """Run Application."""
    default_config_file = Path(__file__).name.replace(".py", ".conf")
    # config file in /etc gets overriden by the one in /etc/tasks_from_email which gets
    # overridden by the one in $HOME which gets overriden by the one in the current
    # directory
    default_config_files = [
        "/etc/" + default_config_file,
        "/etc/" + default_config_file.replace(".conf", "") + "/" + default_config_file,
        Path("~").expanduser() / default_config_file,
        default_config_file,
    ]
    parser = ArgumentParser(
        default_config_files=default_config_files,
        description="Kanboard Tasks from Email.",
    )
    args = get_arguments(parser)

    imap_connection = imap_connect(
        args.IMAPS_SERVER, args.IMAPS_USERNAME, args.IMAPS_PASSWORD
    )
    typ, data = imap_search_unseen(imap_connection)

    for num in data[0].split():
        """ for each unread mail do """
        typ, data = imap_connection.fetch(num, "(RFC822)")
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        local_task_start_date_iso8601 = convert_to_kb_date(email_message["Date"])
        local_task_due_date_iso8601 = convert_to_kb_date(
            email_message["Date"], args.KANBOARD_TASK_DUE_OFFSET_IN_HOURS
        )
        email_from = email_message["From"]
        """ extract email address if specified as 'name <email address>' """
        email_address = re.sub("[<>]", "", re.findall("\S+@\S+", email_from)[-1])
        email_to = email_message["To"]
        subject = email.header.make_header(
            email.header.decode_header(email_message["Subject"])
        )

        body, kb_attachments = walk_message_parts(email_message)

        email_address, local_task_start_date_iso8601, local_task_due_date_iso8601 = (
            handle_well_known_forwarders(
                args.WELL_KNOWN_EMAIL_ADDRESSES,
                args.KANBOARD_TASK_DUE_OFFSET_IN_HOURS,
                body,
                email_address,
                local_task_start_date_iso8601,
                local_task_due_date_iso8601,
            )
        )

        kb_text = dedent(f"""
                         From: {email_from}

                         To: {email_to}

                         Date: {local_task_start_date_iso8601}

                         Subject: {subject}

                         {body}""").lstrip()

        """ connect to kanboard api """
        kb = kanboard.Client(
            args.KANBOARD_CONNECT_URL + "/jsonrpc.php",
            "jsonrpc",
            args.KANBOARD_API_TOKEN,
        )

        kb_user_id = create_user_for_sender(kb, email_address)

        """ add user to group """
        if (
            args.KANBOARD_GROUP_ID > 0
        ):  # pragma: no cover - will get tested once config is refactored
            kb.add_group_member(group_id=args.KANBOARD_GROUP_ID, user_id=kb_user_id)

        """ get id from project specified """
        kb_project_id = kb.get_project_by_name(name=str(args.KANBOARD_PROJECT_NAME))[
            "id"
        ]

        kb_task_id, kb_task = get_task_if_subject_matches(kb, subject)

        if kb_task:
            reopen_and_update(
                kb,
                kb_task,
                kb_task_id,
                kb_user_id,
                kb_text,
                local_task_due_date_iso8601,
            )
        else:
            """ create task in project specified """
            kb_task_id = kb.create_task(
                project_id=str(kb_project_id),
                title=str(subject),
                creator_id=kb_user_id,
                date_started=local_task_start_date_iso8601,
                date_due=local_task_due_date_iso8601,
                description=kb_text,
            )

        """ add the email as an attachment to the task in case it's not properly
            displayed in the description or comment """
        if kb_task_id:
            kb_attachments["%s.mbox" % re.sub("[^\w_.)( -]", "_", str(subject))] = (
                base64.b64encode(raw_email)
            )
            for i in kb_attachments:
                kb.create_task_file(
                    project_id=str(kb_project_id),
                    task_id=str(kb_task_id),
                    filename=i,
                    blob=kb_attachments[i].decode("utf-8"),
                )

    imap_close(imap_connection)


if __name__ == "__main__":  # pragma: no cover
    main()
