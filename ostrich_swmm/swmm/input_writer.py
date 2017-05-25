"""Functionality for writing a SWMM input file."""

from __future__ import print_function

from . import input as si


def format_line_for_write(data, comment):
    """Format a line's contents for writing to a SWMM input file.

    Args:
        data (string): The data portion of the line, preformatted as a string.
        comment (string|None): The comment portion of the line.

    Returns:
        string: A string ready to be written to a file.
    """
    if comment is None:
        return data

    return '{0};{1}'.format(data, comment)


def format_value_for_write(value, section_format):
    """Format a given value for outputting to a SWMM input file.

    Args:
        value (mixed): The value to write out.
        section_format (string): The format of the section of the input file.

    Returns:
        string: The string to write out to the file.

    Raises:
        ValueError: The format is unknown.
    """
    if section_format == 'txt':
        return str(value)
    elif section_format == 'ssv':
        value_str = str(value)
        if not value_str.startswith('"') and ' ' in value_str:
            value_str = '"{0}"'.format(value_str)
        return value_str
    else:
        raise ValueError("Unknown section format: {0}".format(section_format))


def write(content, f):
    """Write the contents of a SWMM input file into a file.

    Args:
        content (dict): The SWMM input file contents.
        f (file): The file to write to.
    """
    for section, section_content in content.iteritems():
        # Print the section header if it exists.
        is_empty_section = section == ''
        if not is_empty_section:
            section_comment = section_content['comment']
            print(format_line_for_write(
                '[{0}]{1}'.format(
                    section,
                    '' if section_comment is None else ' ',
                ),
                section_comment,
            ), file=f)

        # If this section has no content...
        lines = section_content['lines']
        if not lines:
            # If this is not the "empty" section, print an empty line.
            if not is_empty_section:
                print('', file=f)

            # Continue to the next section.
            continue

        # Pad shorter lines out with empty strings to make lines equal length.
        max_line_length = max(len(line['values']) for line in lines)
        lines_values = [
            line['values'] + ([''] * (max_line_length - len(line['values'])))
            for line
            in lines
        ]

        # Convert any non-string values to strings.
        section_format = si.get_section_format(section)
        lines_value_strings = [
            [
                format_value_for_write(value, section_format)
                for value
                in line_values
            ]
            for line_values
            in lines_values
        ]

        # Figure out the maximum string length of each column.
        column_widths = [
            max(map(len, column))
            for column
            in zip(*lines_value_strings)
        ]
        soft_tab_width = 4
        pretty_column_widths = [
            w + (soft_tab_width - (w % soft_tab_width)) - 1
            for w
            in column_widths
        ]

        # Print each line in the section.
        for line, line_value_strings in zip(lines, lines_value_strings):
            line_comment = line['comment']
            line_data_str = ' '.join(
                value.ljust(column_width)
                for value, column_width
                in zip(line_value_strings, pretty_column_widths)
            ).rstrip()

            if line_data_str != '' and line_comment is not None:
                line_data_str = '{0} '.format(line_data_str)

            print(format_line_for_write(
                line_data_str,
                line_comment,
            ), file=f)

        # Print a blank line at the end of the section for readability.
        print('', file=f)
