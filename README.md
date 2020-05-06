# Simple script to create kanboard tasks from email
Simple script to create kanboard tasks from email.

___The code is in its early stages and specifically made for a particular use-case. It's not (yet) good-to-go. Don't use it unless you're experienced in using python.___


## Introduction
This scripts creates [kanboard](https://kanboard.org/) tasks from unread mails through the API using the official [python API client](https://github.com/kanboard/python-api-client). The reason for this script was to use kanboard as a very simple helpdesk used via email. This script is solely being used for that purpose.


## How it works
Description of the procedure:
1. An email is sent to a dedicated support address, e.g. support@mydomain.local (Settings: ```IMAPS_.*```)
2. The script checks if the email is forwarded from a well-known addres, like e.g. it@mydomain.local defined in ```WELL_KNOWN_EMAIL_ADDRESSES```. Sometimes people send emails to other well-known email addresses in the company. If this is the case, the script is looking for the sender email address within the email body. Otherwise the sender email will be the the email address taken from the email headers.
3. If the subject of the email contains the task number in the format ```KB#\d+```, the task will be reopened if it was closed before and the email will be added as comment to this task. Ohterwise a new task will be created. The task will be added to the project defined in ```KANBOARD_PROJECT_NAME```. The due date will be set by the offset defined in ```KANBOARD_TASK_DUE_OFFSET_IN_HOURS```.
4. Attachments of the email will be added as attachments to the task.
5. An mbox file of the original raw email will be added as attachment as well in case the plain/text part of an email is broken or in some strange character encoding.
6. The creator of the email will be set to an existing user if the email address already belongs to one. Otherwise a new user will be created. This allows by using the kanboard plugin [ExtendedMail](https://github.com/atcomputing/kanboard-ExtendedMail) and/or automatic actions to predefine the creator e.g. as a recipient of "comments by email".


## Installation
1. Install python 3.6 and pip
2. Install kanboard using pip
3. Copy the files the destination you want to run the script
4. Adjust the settings in [tasks_from_email_config.py](https://github.com/radiorabe/kanboard-tasks-from-email/blob/master/src/tasks_from_email_config.py)

TODO: more detailed instructions

TODO: systemd unit

TODO: installation package

TODO: re-organize code

## Development

### Testing

This projects uses [pytest](https://pytest.org). The tests are in the main `src/` directory.

You need to install some test tooling using `pip`:

```bash
pip install -r requirements-dev.txt
```

Next you can run the tests:

```bash
pytest
```
