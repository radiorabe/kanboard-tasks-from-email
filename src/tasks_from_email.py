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


""" Import libraries and config file """
import os, sys, imaplib, email, datetime, mailbox, kanboard, ssl, re, time, base64
sys.path.append('/etc/tasks_from_email')
try:
    from tasks_from_email_config import *
except ImportError:
    if os.path.exists('/etc/tasks_from_email'):
        print('ERROR: Make sure tasks_from_email_config.py exists in "/etc/task_from_email", are readable and contain valid settings.')
    else:
        print('ERROR: The path "/etc/tasks_from_email" where the settings are kept, does not exist.')
    exit(1)

def convert_to_kb_date(date_str, increment_by_hours=0):
    """convert a date into a kanboard compatible date

    Parameters
    ----------
    date_str: str, mandatory
        String containing a date from an email (tested with emails only)
    increment_by_hours: int, optional
        Number of hours offset to date_str
    
    Returns
    -------
    string
        the date in kanboard compatible format %d.%m.%Y %H:%M
    """
    local_kb_date = None
    date_tuple = email.utils.parsedate(date_str)
    """ add 12 hours if the passed date string is in 12-hours format and ends with 'PM' """
    if date_str[-2:] == 'PM':
        increment_by_hours += 12
    if date_tuple:
        local_timezone = datetime.datetime.now(datetime.timezone(datetime.timedelta(0))).astimezone().tzinfo
        local_date = datetime.datetime.fromtimestamp(time.mktime(date_tuple), local_timezone)
        if increment_by_hours > 0:
            local_date = local_date + datetime.timedelta(hours=increment_by_hours)
        local_kb_date = "%s" %(str(local_date.strftime('%d.%m.%Y %H:%M')))
    return local_kb_date

def reopen_and_update(kb, kb_task, kb_task_id, kb_user_id, kb_text, local_task_due_date_ISO8601):
    """ reopen task, update due date and add email as comment """
    if kb_task['is_active'] == 0:
        kb.open_task(task_id=kb_task_id)
    """ add email as comment """
    kb.create_comment(task_id=kb_task_id, user_id=kb_user_id, content=kb_text)
    kb.update_task(id=kb_task_id, date_due=local_task_due_date_ISO8601)

def main():
    """ connect and authenticate against mailserver """
    imap_connection = imaplib.IMAP4_SSL(IMAPS_SERVER)
    imap_connection.login(IMAPS_USERNAME, IMAPS_PASSWORD)

    """ get unread mails """
    imap_connection.select('INBOX')
    typ, data = imap_connection.search(None, 'unseen')

    for num in data[0].split():
        """ for each unread mail do """
        typ, data = imap_connection.fetch(num, '(RFC822)')
        raw_email = data[0][1]
        email_message = email.message_from_bytes(raw_email)

        local_task_start_date_ISO8601 = convert_to_kb_date(email_message['Date'])
        local_task_due_date_ISO8601 = convert_to_kb_date(email_message['Date'], 
                                                         KANBOARD_TASK_DUE_OFFSET_IN_HOURS)
        email_from = email_message['From']
        """ extract email address if specified as 'name <email address>' """
        email_address=re.sub('[<>]', '', re.findall('\S+@\S+', email_from)[-1])
        email_to = email_message['To']
        subject = email.header.make_header(email.header.decode_header(email_message['Subject']))

        kb_attachments = {}

        for part in email_message.walk():
            """ get plain text body details """
            if part.get_content_maintype() == 'multipart':
                continue
            if part.get('Content-Disposition') is None:
                if part.get_content_type() == 'text/plain':
                    body = re.sub('\r\n', '\r\n\r\n', part.get_payload(decode=True).decode('utf-8'))
                continue
            fileName = email.header.make_header(email.header.decode_header(part.get_filename()))
            if bool(fileName):
                kb_attachments[str(fileName)] = base64.b64encode(part.get_payload(decode=True))
                body = '%s\n\n<< Attachment: %s >>' %(body, fileName)

        """ if the email has been forwarded from specified addresses use sender 
            email address and timestamp from message body """
        fwd_email_addresses=re.findall('(From:.*\S+@\S+|To:.*\S+@\S+)', '%s' % body)
        if fwd_email_addresses:
            fwd_to_email_address=re.sub('[<>]', '', re.findall('\S+@\S+', fwd_email_addresses[1])[-1])
            if fwd_to_email_address in WELL_KNOWN_EMAIL_ADDRESSES:
                email_address = re.sub('[<>]', '', re.findall('\S+@\S+', fwd_email_addresses[0])[-1])
                local_task_start_date_ISO8601 = convert_to_kb_date(re.sub('Date:\s*',
                                                                          '',
                                                                          re.search('Date:[\S ]+',
                                                                                    '%s' % body,
                                                                                    re.MULTILINE).group(0)))
                local_task_due_date_ISO8601 = convert_to_kb_date(re.sub('Date:\s*',
                                                                        '',
                                                                        re.search('Date:[\S ]+',
                                                                                  '%s' % body,
                                                                                  re.MULTILINE).group(0)),
                                                                 KANBOARD_TASK_DUE_OFFSET_IN_HOURS)

        kb_text = 'From: %s\n\nTo: %s\n\nDate: %s\n\nSubject: %s\n\n%s' % (email_from, 
                                                                           email_to, 
                                                                           local_task_start_date_ISO8601, 
                                                                           subject, 
                                                                           body)

        """ connect to kanboard api """
        kb = kanboard.Client(KANBOARD_CONNECT_URL+'/jsonrpc.php', 'jsonrpc', KANBOARD_API_TOKEN)

        """ create user for sender email if it doesn't exist """
        kb_user_id = None
        kb_users = kb.get_all_users()
        for kb_user in kb_users:
            if kb_user['email'] == email_address:
                kb_user_id = kb_user['id']
        if kb_user_id == None:
            kb_user_id = kb.create_user(username=email_address, password=email_address, email=email_address)

        """ add user to group """
        if KANBOARD_GROUP_ID > 0:
            kb.add_group_member(group_id=KANBOARD_GROUP_ID, user_id=kb_user_id)

        """ get id from project specified """
        kb_project_id = kb.get_project_by_name(name=str(KANBOARD_PROJECT_NAME))['id']

        """ search for link to already existing task """
        kb_task_search_result = re.findall('\[KB#\d+', '%s' % subject)
        kb_task = None
        if kb_task_search_result:
            kb_task_id = re.sub('\[KB#', '', kb_task_search_result[-1])
            """ test if task already exists """
            kb_task = kb.get_task(task_id=kb_task_id)

        if kb_task:
            reopen_and_update(kb, kb_task, kb_task_id, kb_user_id, kb_text, local_task_due_date_ISO8601)
        else:
            """ create task in project specified """
            kb_task_id = kb.create_task(project_id=str(kb_project_id), 
                                                       title=str(subject), 
                                                       creator_id=kb_user_id, 
                                                       date_started=local_task_start_date_ISO8601, 
                                                       date_due=local_task_due_date_ISO8601, 
                                                       description=kb_text)

        """ add the email as an attachment to the task in case it's not properly displayed 
            in the description or comment """
        if kb_task_id != False:
            kb_attachments['%s.mbox' % re.sub('[^\w_.)( -]', '_', str(subject))] = base64.b64encode(raw_email)
            for i in kb_attachments:
                kb.create_task_file(project_id=str(kb_project_id), 
                                    task_id=str(kb_task_id), 
                                    filename=i, 
                                    blob=kb_attachments[i].decode('utf-8'))

    """ close mailserver connection """
    imap_connection.close()
    imap_connection.logout()

if __name__ == "__main__":
    main()
