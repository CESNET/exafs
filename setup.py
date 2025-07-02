import setuptools
import os


def read_requirements(filename="requirements.txt"):
    """Read requirements from requirements.txt file."""
    if not os.path.exists(filename):
        return []

    requirements = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            # Skip empty lines and comments
            if line and not line.startswith("#"):
                # Handle requirements with comments
                if "#" in line:
                    line = line.split("#")[0].strip()
                requirements.append(line)
    return requirements


# Import the __version__ variable
with open("flowapp/__about__.py") as f:
    exec(f.read())

setuptools.setup(
    name="exafs",
    version=__version__,  # noqa: F821
    author="CESNET / Jiri Vrany, Petr Adamec, Josef Verich, Jakub Man",
    description="Tool for creation, validation, and execution of ExaBGP messages.",
    url="https://github.com/CESNET/exafs",
    license="MIT",
    py_modules=["flowapp"],
    packages=setuptools.find_packages(),
    include_package_data=True,
    python_requires=">=3.11",
    install_requires=read_requirements(),
)
