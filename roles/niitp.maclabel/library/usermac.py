#!/usr/bin/python

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

DOCUMENTATION = r'''
---
module: usermac

short_description: Setting the user mandatory attributes.

version_added: "1.0.0"

description: Installation of mandatory user attributes in the Astra Linux OS.

options:
    user:
        description: Username.
        required: true
        type: str
    min:
        description: Min mandatory attributes.
        required: false
        type: int
        default: 0

    max:
        description: Max mandatory attributes.
        required: false
        type: int
        default: 2

author:
    - Nikita Sychev (@sychev)
'''

EXAMPLES = r'''
- name: Change max mandatory attributes
  niitp.maclabel.usermac:
    user: tasp
    max: 2
'''
import pwd
import subprocess
from enum import IntEnum
from typing import Tuple
from ansible.module_utils.basic import AnsibleModule


def run_module():
    module_args = dict(
        user=dict(type='str', required=True),
        min=dict(type='int', required=False, default=0),
        max=dict(type='int', required=False, default=2)
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=True
    )

    result = {
        "changed": False,
    }

    usermac = Usermac(module.params['user'])
    status, message = usermac.change_maclabel(module.params['min'], module.params['max'])
    if status == ExitStatus.error:
        module.fail_json(msg=message)

    result['changed'] = status.value
    module.exit_json(**result)

class ExitStatus(IntEnum):

    ok = 0
    changed = 1
    error = 2

class Usermac:
    def __init__(self, user):
        self.__user = user
        try:
            user = pwd.getpwnam(self.__user)
            self.__uid = user.pw_uid
        except KeyError:
            self.__uid = -1

    def change_maclabel(self, min: int, max: int):
        try:
            self.__validate(min, max)
        except Exception as message:
            return ExitStatus.error, message.args

        current_min, current_max = self.__read_maclabel()
        if current_min != min or current_max != max:
            subprocess.run(['usermac', '-l', f'{min}:{max}', self.__user])
            return ExitStatus.changed, ''

        return ExitStatus.ok, ''

    def __validate(self, min, max):
        if min < 0 or max < 0:
            raise Exception('Negative number')

        if min >  max:
            raise Exception('Min > Max')

        if self.__uid == -1:
            raise Exception('User not found')

    def __read_maclabel(self) -> Tuple[int, int]:
        try:
            with open(f'/etc/parsec/macdb/{self.__uid}') as f:
                macdb = f.readline()
        except FileNotFoundError:
            return -1, -1

        elements = macdb.split(':')
        return int(elements[1]), int(elements[3])

def main():
    run_module()

if __name__ == '__main__':
    main()
