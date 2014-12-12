#!/usr/bin/env python2
# -*- coding: utf-8 -*-

import grp
import os
import pwd

def drop_privs(uid_name='eventbot', gid_name='eventbot'):
    if os.getuid() != 0:
        # We're not root, so bail
        return

    # Get the uid/gid from the name
    running_uid = pwd.getpwnam(uid_name).pw_uid
    running_gid = grp.getgrnam(gid_name).gr_gid

    # Remove group privileges
    os.setgroups([])

    # Try settings the new uid/gid
    os.setgid(running_gid)
    os.setuid(running_uid)

    # Ensure a very conservative mask
    old_umask = os.umask(077)
