"""Functionality for reading a SWMM input file."""

from collections import OrderedDict
import re
import shlex

from . import input as si


def read(f):
    """Read the contents of a SWMM input file into memory.

    Args:
        f (file): The file to read.

    Returns:
        OrderedDict: The input data, structured similar to how it's written.
            Each key is a section header in all-caps, and each value is an
            object with a list of lines and any comment for that section.
            Each line is an object with a list of values and any comment.
    """
    file_dict = OrderedDict({
        '': {
            'lines': [],
            'comment': None,
        },
    })
    current_section = ''
    current_section_format = si.get_section_format(current_section)
    current_section_lines = file_dict[current_section]['lines']
    for line in f:
        # Split the line into data and comment.
        line_parts = line.split(';', 1)
        line_data = line_parts[0].rstrip('\r\n')
        line_comment = (
            line_parts[1].rstrip('\r\n')
            if len(line_parts) > 1
            else None
        )

        # If the line starts with "[", it is a section header.
        if line.startswith('['):
            section_re_match = re.search(r'\[(?P<section>[^\]]*)\]', line_data)
            current_section = section_re_match.group('section').upper()
            current_section_format = si.get_section_format(
                current_section,
            )
            if current_section not in file_dict:
                file_dict[current_section] = {
                    'lines': [],
                    'comment': line_comment,
                }
            current_section_lines = file_dict[current_section]['lines']
            continue

        # If the line is not a section header, parse it as a line according to
        # the section's formatting.
        if current_section_format == 'ssv':
            line_parser = shlex.shlex(line_data)
            line_parser.commenters = ''
            line_parser.whitespace_split = True
            line_values = list(line_parser)
        else:
            line_values = [line_data]

        current_section_lines.append({
            'values': line_values,
            'comment': line_comment,
        })

    return file_dict
