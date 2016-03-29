#!/usr/bin/env python
from setuptools import find_packages, setup

project = "microcosm-dynamodb"
version = "0.1.0"

setup(
    name=project,
    version=version,
    description="Opinionated persistence with dynamodbQL",
    author="Globality Engineering",
    author_email="engineering@globality.com",
    url="https://github.com/globality-corp/microcosm-dynamodb",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    zip_safe=False,
    keywords="microcosm",
    install_requires=[
        "boto3>=1.3.0",
        "microcosm>=0.4.0",
    ],
    setup_requires=[
        "nose>=1.3.6",
    ],
    dependency_links=[
    ],
    entry_points={
        "microcosm.factories": [
            "sessionmaker = microcosm_dynamodb.factories:configure_dynamodb_sessionmaker",
        ],
    },
    tests_require=[
        "coverage>=3.7.1",
        "mock>=1.0.1",
        "PyHamcrest>=1.8.5",
    ],
)
