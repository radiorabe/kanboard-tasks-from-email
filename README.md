# kanboard-tasks-from-email
Simple script to create kanboard tasks from email.

___The code is in its early stages and specifically made for a particular use-case. It's not (yet) good-to-go. Don't use it unless you're experienced in using python.___

## Introduction
This scripts creates [kanboard](https://kanboard.org/) tasks from unread mails through the API using the official [python API client](https://github.com/kanboard/python-api-client). The reason for this script was to use kanboard as a very simple helpdesk used via email. This script is solely being used for that purpose.


## How it works
This script creates a task or adds a comment to an existing task after an email to the configured adddress was sent. If the email contains a link to an existing task, the new email is added to this task as a comment. Received emails also get attached to the task in case it's not properly getting displayed. E.g. because of character encoding issues.


If an email was sent to a wrong but known address, the body of the email will be search for the contact information.


For each email received from a new address, a user will be created so he can receive notifications.


## Installation
1. Install python 3.6 and pip
2. Install kanboard using pip
3. Copy the files the destination you want to run the script
4. Adjust the settings in [tasks_from_email_config.py](https://github.com/radiorabe/kanboard-tasks-from-email/blob/master/src/tasks_from_email_config.py)

TODO: more detailed instructions

TODO: systemd unit

TODO: installation package

TODO: re-organize code
