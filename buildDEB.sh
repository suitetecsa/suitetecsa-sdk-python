#!/bin/sh
mkdir -p PyLibSuitETECSA_0.1.0-1_all//DEBIAN
cp BuildDEB/* PyLibSuitETECSA_0.1.0-1_all//DEBIAN
mkdir -p PyLibSuitETECSA_0.1.0-1_all/usr/lib/python3/dist-packages/libsuitetecsa/core/
cp libsuitetecsa/__init__.py PyLibSuitETECSA_0.1.0-1_all/usr/lib/python3/dist-packages/libsuitetecsa/__init__.py
cp libsuitetecsa/__about__.py PyLibSuitETECSA_0.1.0-1_all/usr/lib/python3/dist-packages/libsuitetecsa/__about__.py
cp libsuitetecsa/api.py PyLibSuitETECSA_0.1.0-1_all/usr/lib/python3/dist-packages/libsuitetecsa/api.py
cp libsuitetecsa/core/exception.py PyLibSuitETECSA_0.1.0-1_all/usr/lib/python3/dist-packages/libsuitetecsa/core/exception.py
cp libsuitetecsa/core/__init__.py PyLibSuitETECSA_0.1.0-1_all/usr/lib/python3/dist-packages/libsuitetecsa/core/__init__.py
cp libsuitetecsa/core/models.py PyLibSuitETECSA_0.1.0-1_all/usr/lib/python3/dist-packages/libsuitetecsa/core/models.py
chmod 775 -R PyLibSuitETECSA_0.1.0-1_all//DEBIAN/
dpkg-deb -b PyLibSuitETECSA_0.1.0-1_all/
rm -r PyLibSuitETECSA_0.1.0-1_all/
