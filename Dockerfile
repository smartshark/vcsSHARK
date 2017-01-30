FROM ubuntu:16.04

RUN apt-get update
RUN apt-get install -y build-essential wget git
RUN apt-get install -y python3-pip python3-cffi libgit2-24 libgit2-dev


RUN git clone https://github.com/smartshark/vcsSHARK /root/vcsshark