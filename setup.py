from setuptools import setup
import os
import re

def find_version():
    with open('pionUploader.py', 'r') as version_file:
        version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]",
                                  version_file.read(), re.M)
        if version_match:
            return version_match.group(1)
        raise RuntimeError("Unable to find version string.")

if os.name == "nt":
    scripts = None
    entry_points = {
        {
        'console_scripts': ['tasmotizer=tasmotizer:main'],
        }
    }
else:
    scripts = ['pionUploader.py']
    entry_points = None

setup(
    name='PionUpploader',
    version=find_version(),
    url='https://github.com/pion-labs/pion-kits-firmware-uploader',
    py_modules=['pionUploader', 'gui', 'pionUploader_esptool', 'banner', 'utils'],
    license='GPLv3',
    author='Pion Labs',
    author_email='liftoff@pionlabs.com.br',
    description='Firmware uploader for PION Educational kits!',
    long_description="Dedicated flashing tool for the default firmware for PION Educational Satellite Kits",
    python_requires='>=3.6',
    install_requires=[
        "pyserial>=3.0",
        "PyQt5>=5.10"
    ],
    entry_points=entry_points,
    scripts=scripts,
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: OS Independent",
    ],
    project_urls={
        "Issue Tracker": "https://github.com/pion-labs/pion-kits-firmware-uploader/issues",
        "Documentation": "https://github.com/pion-labs/pion-kits-firmware-uploader/wiki",
    },
)
