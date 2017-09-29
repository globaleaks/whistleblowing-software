#!/usr/bin/env python
# -*- coding: utf-8 -*-

import re
import sys

import pip
from pkg_resources import parse_version


def version_number_compare(version1, version2):
    return cmp(parse_version(version1), parse_version(version2))

def pip_version_check(path):
    installed_packages = dict()
    for dist in pip.get_installed_distributions(local_only=False):
        installed_packages[dist.project_name.lower()] = dist.version

    p = re.compile('\s*(?P<package>[a-zA-Z0-9_.]+)(?P<condition>[<=>]{2}|[<>]{1})(?P<version>\S+)')
    unmet_requirements = []
    with open(path, "r") as rf:
        for requirement in rf.readlines():
            match = p.match(requirement.strip())
            if match is not None:
                continue

            package = match.group('package').lower()
            version = match.group('version')
            condition = match.group('condition')

            if package in installed_packages:
                pass
            elif package.replace('_', '-') in installed_packages:
                package = package.replace('_', '-')
            else:
                unmet_requirements.append([requirement, ""])
                continue

            installed_version = installed_packages[package]

            check = version_number_compare(installed_version, version)
            if condition == "<":
                if check >= 0:
                    unmet_requirements.append([requirement, installed_version])
            elif condition == "<=":
                if check > 0:
                    unmet_requirements.append([requirement, installed_version])
            elif condition == "==":
                if check != 0:
                    unmet_requirements.append([requirement, installed_version])
            elif condition == ">=":
                if check < 0:
                    unmet_requirements.append([requirement, installed_version])
            elif condition == ">":
                if check <= 0:
                    unmet_requirements.append([requirement, installed_version])

    if unmet_requirements:
        print("Some GlobaLeaks requirements are unmet\n")
        print("Unmet requirements:")
        for unmet_requirement_desc in unmet_requirements:
            if unmet_requirement_desc[1]:
                print("\t", unmet_requirement_desc[0] + " [ Installed", unmet_requirement_desc[1], "]")
            else:
                print("\t", unmet_requirement_desc[0])

        print("\n")
        print("The problem can be solved by:")
        print("1) Following the guidelines at https://github.com/globaleaks/GlobaLeaks/wiki")
        print("2) Installing missing requirements using rm -rf /tmp/pip-build-root/ && pip install -r /usr/share/globaleaks/requirements.txt")

        sys.exit(54)
