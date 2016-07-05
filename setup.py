#!/usr/bin/env python
from setuptools import find_packages, setup

project = "microcosm-dynamodb"
version = "0.9.0"

setup(
    name=project,
    version=version,
    description="Opinionated persistence with DynamoDB",
    long_description="Opinionated persistence with DynamoDB",
    author="Globality Engineering",
    author_email="engineering@globality.com",
    classifiers=[
        'Intended Audience :: Developers',
    ],
    download_url='http://pypi.python.org/pypi/microcosm-dynamodb',
    keywords=[
        'microcosm',
        'dynamodb',
    ],
    license='Apache v2.0 License',
    platforms='Linux',
    url="https://github.com/globality-corp/microcosm-dynamodb",
    packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "boto3>=1.3.1",
        "flywheel>=0.4.8",
        "microcosm>=0.9.0",
    ],
    setup_requires=[
        "nose>=1.3.6",
    ],
    dependency_links=[
    ],
    entry_points={
        "microcosm.factories": [
            "dynamodb = microcosm_dynamodb.factories:configure_flywheel_engine",
        ],
    },
    tests_require=[
        "coverage>=3.7.1",
        "mock>=1.0.1",
        "PyHamcrest>=1.8.5",
    ],
)
