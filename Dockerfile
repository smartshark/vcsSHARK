FROM ubuntu:16.04


# Install dependencies
RUN apt-get update
RUN apt-get install -y build-essential wget git
RUN apt-get install -y python3-pip python3-cffi libgit2-24 libgit2-dev

# Get newest pip and setuptools version
RUN pip3 install -U pip setuptools
RUN pip3 install Sphinx
RUN pip3 install sphinx_rtd_theme
RUN pip3 install ghp_import

# Configure GIT
RUN git config --global user.email "smartshark@cs.uni-goettingen.de"
RUN git config --global user.name "Travis CI"

# Clone repository
RUN git clone --recursive https://github.com/smartshark/vcsSHARK /root/vcsshark

# Install vcsshark requirements
RUN pip3 install -r /root/vcsshark/requirements.txt