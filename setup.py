"""Setup script for ostrich_swmm.

Based on Python Packaging User Guide:
https://packaging.python.org/distributing/
"""

from setuptools import find_packages, setup

# Load __version__
with open('ostrich_swmm/version.py', 'r') as version_file:
    exec(version_file.read())

setup(
    name="ostrich_swmm",
    version=__version__,  # noqa: F821
    description=(
        "A toolset for connecting the OSTRICH optimization software toolkit "
        "with the SWMM simulation model."
    ),
    url="https://github.com/ubccr/ostrich-swmm",
    author="Tom Yearke",
    author_email="tyearke@buffalo.edu",
    license="GPL-2.0",
    classifiers=[
        'Development Status :: 2 - Pre-Alpha',
        'Intended Audience :: Science/Research',
        'License :: OSI Approved :: GNU General Public License v2 (GPLv2)',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
    ],
    keywords=(
        'ostrich optimizer optimization swmm storm water stormwater simulation'
    ),
    packages=find_packages(),
    install_requires=[
        'swmmtoolbox>=1.0.5.8,<2',
        'numpy>=1.12,<2',
        'jsonschema>=2.6.0,<3',
        'shapely>=1.5,<2',
        'pint>=0.8,<0.9',
    ],
    package_data={
        '': [
            'data/*',
            'data/schemas/*',
        ]
    },
    entry_points={
        'console_scripts': [
            'ostrich-swmm=ostrich_swmm.__main__:main',
        ],
    },
)
