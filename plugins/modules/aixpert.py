#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2020- IBM, Inc
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = r'''
---
author:
- AIX Development Team (@pbfinley1911)
module: aixpert
short_description: Apply/Check/Save/Undo/Query security settings
description:
- This module facilitates
    a. Application of security rules on the system using aixpert
    b. Checking of security settings
    c. Undo of the previously applied set of security rules
    d. Saving of security rules in normal or abbreviated mode.
version_added: '2.9'
requirements:
- AIX
- Python >= 2.7
- Should be run as 'root' user
options:
  mode:
    description:
    - Specifies the action to be performed
      I(mode=apply), applies the security settings based on the level
         specified or profile provided. If both are provided, 'level'
         will take precedence.
      I(mode=check), checks the security settings against the previously
         applied set of rules or the provided 'profile' file
      I(mode=save), saves the security settings for the level specified
         or based on the specified 'profile' file.
         - If I(abbr_fmt_file), is provided, the security rules are saved in
           the abbreviated file format.
         - If I(norm_fmt_file) is provided, the security rules are saved in
           normal format.
      I(mode=undo), undoes the previously applied security settings.
      I(mode=query), get the type of the profile applied on the system.
    type: str
    choices: [apply, check, save, undo, query]
    required: true
  level:
    description:
    - Specifies the security level settings to be applied or saved.
      I(high) - Specifies high-level security options
      I(low) - Specifies low-level security options.
      I(medium) - Specifies medium-level security options.
      I(default) - Specifies AIX® standards-level security options.
      I(sox-cobit) - Specifies SOX-COBIT best practices-level security options.
    type: str
    choices: [ high, medium, low, default, sox-cobit ]
  profile:
    description:
    - When I(mode=apply), specifies the profile to be applied on the system
    - When I(mode=check), specified the profile to be used to check the
        security settings.
    type: str
  abbr_fmt_file:
    description:
    - When I(mode=save) or I(mode=apply), specifies the file where the
      security settings needs to be saved in abbreviated format.
    type: str
  norm_fmt_file:
    description:
    - When I(mode=apply) or I(mode=save), specifies the file where the
      settings should be saved in normal format.
    type: str

'''

EXAMPLES = r'''
  - name: "Save default level rules in normal format"
    aixpert:
       mode: save
       level: default
       norm_fmt_file: /home/kavana/norm.xml

  - name: "Apply using saved profile"
    aixpert:
       mode: apply
       profile: /home/kavana/norm.xml

  - name: "Undo the settings"
    aixpert:
       mode: undo
'''

RETURN = r'''
msg:
    description: The execution message.
    returned: always
    type: str
rc:
    description: The return code.
    returned: If the command failed.
    type: int
stdout:
    description: The standard output.
    returned: If the command failed.
    type: str
stderr:
    description: The standard error.
    returned: If the command failed.
    type: str
'''

from ansible.module_utils.basic import AnsibleModule
import os


def check_settings(module):
    """
    Checks the security settings against the previously applied set of rules
    param module: Ansible module argument spec.
    return: changed - True/False(check succeeded or not),
            msg - message
    """
    cmd = "aixpert -c "
    profile = module.params["profile"]
    if profile:
        cmd += "-P %s " % profile

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Aixpert security check failed. Command in failure '%s'" % cmd
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    changed = True
    msg = "Aixpert security check completed successfully."
    return changed, msg


def undo_settings(module):
    """
    Undoes the security settings
    param module: Ansible module argument spec.
    return: changed - True/False(settings undone or not),
            msg - message
    """
    cmd = "aixpert -u "
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Unable to undo aixpert settings. Command in failure '%s' " % cmd
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    changed = True
    msg = "aixpert settings undone successfully."
    return changed, msg


def apply_settings(module, mode):
    """
    Apply/save the specified level or provided security settings
    param module: Ansible module argument spec.
    param mode: apply/save
    return: changed - True/False(apply/save of security settings succeeded or not),
            msg - message
    """
    level = module.params["level"]
    abbr_fmt_file = module.params["abbr_fmt_file"]
    norm_fmt_file = module.params["norm_fmt_file"]
    profile = module.params["profile"]

    if profile and not os.path.isfile(profile):
        msg = "Specified profile '%s' doesn't exist" % profile
        return False, msg

    if mode == 'apply' and not level and not profile:
        msg = "Specify either level or profile to apply the security settings"
        return False, msg

    if mode == 'save' and not abbr_fmt_file and not norm_fmt_file:
        msg = "Specify either abbr_fmt_file or norm_fmt_file to save the security settings"
        return False, msg

    if profile and norm_fmt_file:
        msg = "'norm_fmt_file' cannot be specified when 'profile' is provided."
        return False, msg

    cmd = "aixpert "
    if level:
        cmd += "-l %s " % level
        if norm_fmt_file:
            cmd += "-n -o %s " % norm_fmt_file
    elif profile:
        cmd += "-f %s " % profile

    if abbr_fmt_file:
        cmd += " -a -o %s " % abbr_fmt_file

    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Unable to apply or save aixpert settings. Command in failure '%s' " % cmd
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    changed = True
    msg = "aixpert settings applied/saved successfully."
    return changed, msg


def query_settings(module):
    """
    Get the security settings applied on the system
    param module: Ansible module argument spec.
    return: msg - message
    """
    cmd = "aixpert -t"
    rc, stdout, stderr = module.run_command(cmd)
    if rc != 0:
        msg = "Unable to query aixpert settings. Command in failure '%s' " % cmd
        module.fail_json(msg=msg, rc=rc, stdout=stdout, stderr=stderr)

    msg = stdout
    return msg


def main():
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=dict(
            level=dict(type='str', choices=['high', 'medium', 'low', 'default', 'sox-cobit']),
            mode=dict(type='str', required=True, choices=['check', 'undo', 'apply', 'save', 'query']),
            abbr_fmt_file=dict(type='str'),
            norm_fmt_file=dict(type='str'),
            profile=dict(type='str'),
        ),
    )

    mode = module.params['mode']

    if mode == 'check':
        # check the security settings against the previously applied rules
        changed, msg = check_settings(module)
    elif mode == 'undo':
        # Undoes the security settings
        changed, msg = undo_settings(module)
    elif mode == 'query':
        changed = False
        msg = query_settings(module)
    elif mode == 'apply' or mode == 'save':
        # Apply/save the security settings provided by level or profile
        changed, msg = apply_settings(module, mode)
    else:
        changed = False
        msg = "Invalid state '%s'" % mode

    module.exit_json(changed=changed, msg=msg)


if __name__ == '__main__':
    main()
