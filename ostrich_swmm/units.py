"""Common functionality for handling units."""

import pint

registry = pint.UnitRegistry()
"""A UnitRegistry singleton preconfigured with custom rules."""

registry.define('percent = count / 100')
