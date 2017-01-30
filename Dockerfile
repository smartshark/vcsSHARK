FROM ubuntu:16.04


# Install dependencies
RUN apt-get update
RUN apt-get install -y build-essential wget git
RUN apt-get install -y python3-pip python3-cffi libgit2-24 libgit2-dev

# Get newest pip and setuptools version
RUN pip3 install -U pip setuptools

# Clone repository
RUN git clone --recursive https://github.com/smartshark/vcsSHARK /root/vcsshark