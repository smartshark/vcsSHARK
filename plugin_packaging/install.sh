#!/bin/sh
PLUGIN_PATH=$1
cd $PLUGIN_PATH

rpm_installed=$(type -p rpm)
dpkg_query_installed=$(type -p dpkg-query)

if [ ! -z "$rpm_installed" ]; then
  # rmp installed
  PKG_OK=$(rpm -qa | grep libgit2-24)
  PKG_OK_2=$(rpm -qa | grep libgit2-dev)

  if [ ! -z "$PKG_OK" ] && [ ! -z "$PKG_OK_2" ]; then
    cd $PLUGIN_PATH
    # Install vcsshark
    python3.5 $PLUGIN_PATH/setup.py install --user
    exit 0
  fi
fi

if [ ! -z "$dpkg_query_installed" ]; then
  # dpkg_query installed
  PKG_OK=$(dpkg-query -W --showformat='${Status}\n' libgit2-24|grep "install ok installed")
  PKG_OK_2=$(dpkg-query -W --showformat='${Status}\n' libgit2-dev|grep "install ok installed")
  if [ "install ok installed" = "$PKG_OK" ] && [ "install ok installed" = "$PKG_OK_2" ]; then
    cd $PLUGIN_PATH
    # Install vcsshark
    python3.5 $PLUGIN_PATH/setup.py install --user
    exit 0
  fi
fi

# Download libgit
wget --quiet https://github.com/libgit2/libgit2/archive/v0.24.3.tar.gz
tar xzf v0.24.3.tar.gz
cd libgit2-0.24.3/

# Install libgit
if [ -z ${VIRTUAL_ENV+x} ]; then
	cmake .
else
	cmake . -DCMAKE_INSTALL_PREFIX=$VIRTUAL_ENV
fi  

make
make install

# Export new path
# Install libgit
if [ ! -z ${VIRTUAL_ENV+x} ]; then
	export LDFLAGS="-Wl,-rpath='$VIRTUAL_ENV/lib',--enable-new-dtags $LDFLAGS"
fi  

cd $PLUGIN_PATH

# Install vcsshark
python3.5 $PLUGIN_PATH/setup.py install --user