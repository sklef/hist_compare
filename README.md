```
# hist_compare

1) Install ROOT with python

sudo apt-get install subversion dpkg-dev make g++ gcc binutils libx11-dev libxpm-dev libxft-dev libxext-dev

git clone http://root.cern.ch/git/root.git

cd root

git tag -l

git checkout -b v5-34-08 v5-34-08

./configure --enable-python --prefix=/usr/local

sudo make

sudo make install

export LD_LIBRARY_PATH=$ROOTSYS/lib:$PYTHONDIR/lib:$LD_LIBRARY_PATH

export PYTHONPATH=$ROOTSYS/lib:$PYTHONPATH


2) Install rootpy

git clone git://github.com/rootpy/rootpy.git

sudo python setup.py install

3) Install flask

pip install Flask

4) Install request-python

pip install requests
```