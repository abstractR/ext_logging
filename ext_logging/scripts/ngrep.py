#!@PYTHON
import os
import sys
import re

from optparse import OptionParser


def grep(lines, pattern, regexp=False, inverse=False):
    """
    Grep for multiline messages like
    <priority>VERSION ISOTIMESTAMP HOSTNAME APPLICATION PID MESSAGEID STRUCTURED-DATA MSG
    :param pattern: string for matching or regular expression
    :param lines: generator with single line strings
    :param regexp:
    :return: iterator with tuples of lines in message
    """
    next_msg_re = re.compile("<\d{1,2}>1\s\d\d\d\d-\d\d-\d\dT\d\d:\d\d:\d\d.+")
    match_re = re.compile(pattern)
    # each msg can be multiline
    current_msg_lines = []
    matched_msg_lines = []
    for line in lines:
        try:
            # if end or next msg we should to print previous founded msg if it's not []
            if next_msg_re.match(line):
                if inverse:
                    matched_msg_lines = current_msg_lines if not matched_msg_lines else []
                current_msg_lines = []
                # returning previous found msg before trying to find new
                if matched_msg_lines:
                    y = matched_msg_lines
                    matched_msg_lines = []
                    yield y

            # trying to match line by set of criterias
            satisfy_match = match_re.match(line) if regexp else match_re.search(line) if match_re else True
            if satisfy_match:
                matched_msg_lines = current_msg_lines

            current_msg_lines.append(line)
        except KeyboardInterrupt:
            break

        if not line:
            break

    if inverse:
        matched_msg_lines = current_msg_lines if not matched_msg_lines else []
    if matched_msg_lines:
        yield matched_msg_lines


def read_from_stdin():
    input = os.fdopen(sys.stdin.fileno(), 'r', 1)
    while True:
        line = input.readline()
        if line:
            yield line
        else:
            return


def ngrep():
    parser = OptionParser(usage="usage: %prog [param] pattern [file]\n"
                                "Grep for ops logs")
    parser.add_option("-e", action="store_true", dest="regexp", default=False, help="Accept pattern as regexp")
    parser.add_option("-v", action="store_true", dest="inverse", default=False, help="Inverse match")

    (options, args) = parser.parse_args()

    if not args:
        parser.print_help()
        exit(1)
    elif len(args) == 1:
        for i in grep(read_from_stdin(), args[0], regexp=options.regexp, inverse=options.inverse):
            print "".join(i),
    elif len(args) == 2:
        with open(args[1], 'r') as file:
            for i in grep(file, args[0], regexp=options.regexp, inverse=options.inverse):
                print "".join(i),
    else:
        parser.print_help()
        exit(1)

if __name__ == '__main__':
	ngrep()
