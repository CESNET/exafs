"""
Author(s): Jakub Man <Jakub.Man@cesnet.cz>

Setuptools configuration
"""

import setuptools
from flowapp import __version__

setuptools.setup(
    name="exafs",
    version=__version__,
    author="CESNET / Jiri Vrany, Petr Adamec, Josef Verich, Jakub Man",
    description="Tool for creation, validation, and execution of ExaBGP messages.",
    url="https://github.com/CESNET/exafs",
    license="MIT",
    py_modules=["flowapp", "exaapi"],
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.8",
    install_requires=[
        "Flask>=2.0.2",
        "Flask-SQLAlchemy<3.0.0",
        "Flask-SSO>=0.4.0",
        "Flask-WTF>=1.0.0",
        "Flask-Migrate>=3.0.0",
        "Flask-Script>=2.0.0",
        "PyJWT>=2.4.0",
        "PyMySQL>=1.0.0",
        "pytest>=7.0.0",
        "requests>=2.20.0",
        "babel>=2.7.0",
        "mysqlclient>=2.0.0",
        "email_validator>=1.1",
        "pika>=1.3.0",
    ],
)
