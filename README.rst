Electrum-FJC - Lightweight Fujicoin client
==========================================

::

  Licence: MIT Licence
  Original Author: Thomas Voegtlin
  Port Maintainer: Pooler
  Port Maintainer: namuyan (Electrum-FJC)
  Language: Python
  Homepage: https://fujicoin.org/






Getting started
===============

Electrum is a pure python application. If you want to use the
Qt interface, install the Qt dependencies::

    sudo apt-get install python-qt4
    
    sudo pip2 install git+https://github.com/namuyan/fjc-scrypt

If you downloaded the official package (tar.gz), you can run
Electrum from its root directory, without installing it on your
system; all the python dependencies are included in the 'packages'
directory. To run Electrum from its root directory, just do::

    ./electrum-fjc

You can also install Electrum on your system, by running this command::

    python setup.py install

This will download and install the Python dependencies used by
Electrum, instead of using the 'packages' directory.

If you cloned the git repository, you need to compile extra files
before you can run Electrum. Read the next section, "Development
Version".



Development version
===================

Check out the code from Github::

    git clone git://github.com/namuyan/electrum-fjc.git
    cd electrum-fjc

Run install (this should install dependencies)::

    python setup.py install

Compile the icons file for Qt::

    sudo apt-get install pyqt4-dev-tools
    pyrcc4 icons.qrc -o gui/qt/icons_rc.py

Compile the protobuf description file::

    sudo apt-get install protobuf-compiler
    protoc --proto_path=lib/ --python_out=lib/ lib/paymentrequest.proto

Create translations (optional)::

    sudo apt-get install python-pycurl gettext
    ./contrib/make_locale




Creating Binaries
=================


To create binaries, create the 'packages' directory::

    ./contrib/make_packages

This directory contains the python dependencies used by Electrum.
If you get ImportErrors, this is because the modules aren't installed or
are installed, but compressed. Uninstall/install dependencies with pip,
which always installs everything unzipped.

Mac OS X
--------

::

    # On MacPorts installs: 
    sudo python setup-release.py py2app
    
    # On Homebrew installs: 
    ARCHFLAGS="-arch i386 -arch x86_64" sudo python setup-release.py py2app --includes sip
    
    sudo hdiutil create -fs HFS+ -volname "Electrum-FJC" -srcfolder dist/Electrum-FJC.app dist/electrum-fjc-VERSION-macosx.dmg

Windows
-------

See `WINDOWS.md` file.


Android
-------

See `gui/kivy/Readme.txt` file.
