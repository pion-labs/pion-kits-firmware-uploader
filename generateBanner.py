#!/usr/bin/env python
import sys

def main():
    if (len(sys.argv) < 2):
        print("Usage: generateBanner.py <inputFile.png>")
    
    outputfile = """# -*- coding: utf-8 -*-

# Resource object code
#
# Created by: 4m1g0 image compiler for PyQt5 (Qt v5.13.2)


from PyQt5 import QtCore

qt_resource_data = b"\\
\\x00\\x01\\x52\\x0e\\
"""

    with open(sys.argv[1], "rb") as image:
        f = image.read()
        b = bytearray(f)
        column = 0
        for byte in b:
            outputfile += "\\x{:02x}".format(byte)
            if column >= 15:
                outputfile += "\\\n"
                column = 0
            column += 1
        

            
    outputfile += """"

qt_resource_name = b"\\
\\x00\\x0a\\
\\x04\\xc8\\x47\\xe7\\
\\x00\\x62\\
\\x00\\x61\\x00\\x6e\\x00\\x6e\\x00\\x65\\x00\\x72\\x00\\x2e\\x00\\x70\\x00\\x6e\\x00\\x67\\
"

qt_resource_struct_v1 = b"\\
\\x00\\x00\\x00\\x00\\x00\\x02\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x01\\
\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\
"

qt_resource_struct_v2 = b"\\
\\x00\\x00\\x00\\x00\\x00\\x02\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x01\\
\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\
\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01\\x00\\x00\\x00\\x00\\
\\x00\\x00\\x01\\x6e\\xac\\xe0\\x46\\x13\\
"

qt_version = [int(v) for v in QtCore.qVersion().split('.')]
if qt_version < [5, 8, 0]:
    rcc_version = 1
    qt_resource_struct = qt_resource_struct_v1
else:
    rcc_version = 2
    qt_resource_struct = qt_resource_struct_v2

def qInitResources():
    QtCore.qRegisterResourceData(rcc_version, qt_resource_struct, qt_resource_name, qt_resource_data)

def qCleanupResources():
    QtCore.qUnregisterResourceData(rcc_version, qt_resource_struct, qt_resource_name, qt_resource_data)

qInitResources()
"""
    with open("banner.py", "w") as text_file:
        text_file.write(outputfile)

if __name__ == '__main__':
    main()
    

