FROM ubuntu:16.04


# Install dependencies
RUN apt-key adv --keyserver hkp://keyserver.ubuntu.com:80 --recv 0C49F3730359A14518585931BC711F9BA15703C6
RUN echo "deb [ arch=amd64,arm64 ] http://repo.mongodb.org/apt/ubuntu xenial/mongodb-org/3.4 multiverse" | tee /etc/apt/sources.list.d/mongodb-org-3.4.list
RUN apt-get update
RUN apt-get install -y build-essential wget git
RUN apt-get install -y python3-pip python3-cffi libgit2-24 libgit2-dev
RUN apt-get install -y mongodb-org

# Start mongodb
RUN mongod


RUN git clone https://github.com/smartshark/vcsSHARK /root/vcsshark