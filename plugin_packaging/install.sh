#!/bin/sh
PLUGIN_PATH=$1
cd $PLUGIN_PATH

PKG_OK=$(dpkg-query -W --showformat='${Status}\n' libgit2-24|grep "install ok installed")
PKG_OK_2=$(dpkg-query -W --showformat='${Status}\n' libgit2-dev|grep "install ok installed")

if [ "install ok installed" = "$PKG_OK" ] && [ "install ok installed" = "$PKG_OK_2" ]; then
  return 0
fi

# Download libgit
wget https://github.com/libgit2/libgit2/archive/v0.24.0.tar.gz
tar xzf v0.24.0.tar.gz
cd libgit2-0.24.0/

# Install libgit
if [ -z "$VIRTUAL_ENV" ]; then
	cmake . -DCMAKE_INSTALL_PREFIX=$VIRTUAL_ENV
else
	cmake .
fi  

make
make install

# Export new path
# Install libgit
if [ -z "$VIRTUAL_ENV" ]; then
	export LDFLAGS="-Wl,-rpath='$VIRTUAL_ENV/lib',--enable-new-dtags $LDFLAGS"
fi  


# Install vcsshark
python3.5 $PLUGIN_PATH/setup.py install --user