# wander

Migrate users, emails, and contacts from Zimbra email system into Google Apps.

## Installation

    $ pip install git+https://github.com/instituteofdesign/wander.git

## Usage

### Configuration

Copy wander.cfg.example to ~/.wander.cfg or ./wander.cfg and edit the values to match your setup.

### Migrate User Accounts

This will pull down a list of user accounts from your Zimbra server and then create those corresponding accounts on Google Apps. The accounts will use the password specified in your configuration file as the password for all accounts. This is needed to migrate contacts into each users account.

    $ wander accounts

This will pull down a specific users info from Zimbra and create the corresponding account in Google Apps.

    $ wander accounts <username>

### Migrate Contacts

This will migrate all contacts from Zimbra to Google for the specified user at the command-line.

    $ wander contacts <username>

This will migrate all contacts on Zimbra to Google for all users.

    $ wander contacts
