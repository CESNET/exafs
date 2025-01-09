"""
Author(s): 
Jiri Vrany <vrany@cesnet.cz>
Petr Adamec <adamec@cesnet.cz>
Jakub Man <Jakub.Man@cesnet.cz>

Setuptools configuration
"""

import setuptools

# Import the __version__ variable without having to import the flowapp package.
# This prevents missing dependency error in new virtual environments.
with open("flowapp/__about__.py") as f:
    exec(f.read())

setuptools.setup(
    name="exafs",
    version=__version__,  # noqa: F821
    author="CESNET / Jiri Vrany, Petr Adamec, Josef Verich, Jakub Man",
    description="Tool for creation, validation, and execution of ExaBGP messages.",
    url="https://github.com/CESNET/exafs",
    license="MIT",
    py_modules=[
        "flowapp",
    ],
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=[
        "Flask>=2.0.2",
        "Flask-SQLAlchemy>=2.2",
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
