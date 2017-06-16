# Electrum-FJC - Lightweight Fujicoin client


## How to install on Windows  
I use Windows7 Professional 64bit, Python2.7.13 32bit version (automatically 32bit selected, it confuse).  


### install Python2  
![Python2.7 download1](http://imgur.com/hzbueo1.png)  
First of all, download [Python2.7](<https://www.python.org/downloads/>).  
![Python2.7 download2](http://imgur.com/r9KlIwr.png)  
Next, install, DO NOT FORGET TO CHECK PATH!  


### install win_inet_pton and others  
Install win_inet_pton by pip.  
Open CommandPrompt and `pip install win_inet_pton` and `pip install -U setuptools`  


### install PyQt4  
![PyQt4 download](http://imgur.com/5SiW4z5.png)  
Download PyQt4 binary from <https://sourceforge.net/projects/pyqt/files/PyQt4/PyQt-4.10/>.  
Select  *PyQt4-4.10-gpl-Py2.7-Qt4.8.4-x32.exe* , and install PyQt4.  
Next, you need to set PATH, check the PAHT to *QtGui4.dll*, for example `C:\Python27\Lib\site-packages\PyQt4`.
Check the PATH now, `PATH`  
Add PATH to, `Path=%PATH%;C:\Python27\Lib\site-packages\PyQt4`, and close.


### install fjc-scrypt  
Download binary from [fjc-scrypt for Python](https://github.com/namuyan/fjc-scrypt/raw/master/for_windows/fjc_scrypt-1.0.win32-py2.7.exe).  
*Or if you are in any trouble*, please download sorce and compile youself.  
Download from <https://github.com/namuyan/fjc-scrypt>.  
Compile `python setpu.py install`, it's easy.  


### install electrum-fjc  
Download from Github.  
![electrum-fjc download1](http://imgur.com/EThSVZB.png)  
The img is example, check the download file path, and open CommandPrompt and `cd pass\to\electrum-fjc-master`  
Next, `pyrcc4 icons.qrc -o gui/qt/icons_rc.py`, if don't work, you failed to PATH PyQt4.
And install, `python setup.py install`  
Wait for a few minutes....  
![electrum-fjc download2](http://imgur.com/Nfi3bBg.png)  
Next, you need to create shortcut by yourself, and ADD "python".


## trouble shooting  

### unable to find vcvarsall.bat  
Are you compiling? You need VC++ compiler same as Python done version.  
Download and install [Microsoft Visual C++ Compiler for Python 2.7](https://www.microsoft.com/en-us/download/details.aspx?id=44266)  
You need to PATH to, for example `C:\Users\user\AppData\Local\Programs\Common\Microsoft\Visual C++ for Python\9.0`  


### PyQt4.QtGui ImportError: DLL load failed:
Do you correctly PATH to? Check dir of *QtGui4.dll*.  
Or you installed 64bit version, please uninstall and install *32bit* version.  
Default windows python install 32bit version.


## Thank you for reading!
Good fujicoin life!
