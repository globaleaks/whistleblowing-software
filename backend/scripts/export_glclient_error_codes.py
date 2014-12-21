import inspect
import string
import sys
import os
globaleaks_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')
sys.path.append(globaleaks_path)

from globaleaks.rest import errors

def return_exception(klass):
    reason_string = ""
    arguments = inspect.getargspec(klass.__init__).args
    arguments.remove("self")

    if len(arguments) > 0:
        dummy_args = []
        for _ in arguments:
            dummy_args.append("REPLACE_ME")
        kinstance = klass(*dummy_args)
        reason_string = kinstance.reason
    else:
        reason_string = klass.reason

    return {klass.error_code: reason_string}

exceptions = []
for attr in dir(errors):
    klass = getattr(errors, attr)
    if inspect.isclass(klass) and issubclass(klass, errors.GLException):
        exceptions.append(return_exception(klass))

switch_case = """
<div ng-switch on="error.code">
%s
</div>
"""

switch_cases = ""

for exception in exceptions:
    code, exception_str = exception.items()[0]
    exception_strings = ""
    translate = '{{ "%s" | translate }}'
    argument_count = len(exception_str.split("REPLACE_ME")) - 1
    idx = 0
    for reason_string in exception_str.split("REPLACE_ME"):
        reason_string = reason_string.strip()
        skip = False
        if string == "":
            skip = True

        if not skip and any(c in string.ascii_letters for c in reason_string):
            exception_strings += translate % reason_string
        elif not skip:
            exception_strings += reason_string

        if argument_count > idx:
            exception_strings += "{{error.arguments[%s]}}" % idx
            idx += 1

    switch_cases += '<div ng-switch-when="%s">\n%s\n</div>\n\n' % (code, exception_strings)

print switch_case % switch_cases
