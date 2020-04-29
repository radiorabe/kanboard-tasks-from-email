################################################################################
# tasks_from_email_config.py - Configuration file for tasks_from_email.py
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
# Configuration file containing all necessary parameters to run 
# tasks_from_email_config.py.
#
# Usage:
# python3 tasks_from_email.py
#


#
# IMAPS Server connection information
#

# fqdn of mail server
IMAPS_SERVER = ''

# imap user name
IMAPS_USERNAME = ''

# imap user password
IMAPS_PASSWORD = '' # imap user password


#
# kanboard related settings
#

# url for API requests
KANBOARD_CONNECT_URL = ''

# if the url for user interaction difers, e.g. for users kanboard
# is behind a reverse proxy.
KANBOARD_PUBLIC_URL = KANBOARD_CONNECT_URL

# API token from a user that is allowed to create tasks
# 
KANBOARD_API_TOKEN = ''

# Number of hours the task is due after mail received
KANBOARD_TASK_DUE_OFFSET_IN_HOURS = 48

# ID of group new users shall be added to. If set to 0, the new 
# user won't be added to a group.
KANBOARD_GROUP_ID = 0 

# Name of the kanboard project where new tasks are going to be created.
KANBOARD_PROJECT_NAME = 'Support'

#
# various
#
# well-known mail addresses from where emails could be forwarded because they
# were sent to the wrong address
WELL_KNOWN_EMAIL_ADDRESSES = []
