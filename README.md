
# hist_compare

Repository contains client and server app. You can install only client or only server part.

Instalation of server requier ROOT library:
1) Install ROOT with python
```
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
```

After this server can be installed. Move to ./server and run:
```
[sudo] python setup.py install
```

For starting server
```
python api.py
```


For client installation move to ./client and run:
```
[sudo] python setup.py install
```
4) Example
```
import hist_client
first_file = 'default_1.root'
second_file = 'BrunelDaVinci_FULL_134363_00021387.root'
all_paths = ['Timing/OverallEventProcTime/overallTime']
print hist_client.hist_compare(first_file, second_file, all_paths)
```
