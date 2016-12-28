#!/usr/bin/env python
from setuptools import find_packages, setup

project = "microcosm-dynamodb"
version = "0.14.2"

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
        "boto3>=1.4.0",
        "credstash>=1.13.1",
        "flywheel>=0.5.0",
        "microcosm>=0.12.0",
        "microcosm-logging>-0.9.3",
    ],
    setup_requires=[
        "nose>=1.3.7",
    ],
    dependency_links=[
    ],
    entry_points={
        "console_scripts": [
            "create_config_table = microcosm_dynamodb.loaders.operations:create_config_table",
        ],
        "microcosm.factories": [
            "dynamodb = microcosm_dynamodb.factories:configure_flywheel_engine",
        ],
    },
    tests_require=[
        "coverage>=3.7.1",
        "mock>=2.0.0",
        "PyHamcrest>=1.9.0",
    ],
)
