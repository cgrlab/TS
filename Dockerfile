FROM iontorrent/tsbuild

RUN apt-get update
RUN apt-get install curl
RUN git config --global http.sslVerify false
RUN cd /opt/ && git clone https://github.com/iontorrent/TS.git
RUN cd /opt/TS && MODULES='Analysis' ./buildTools/build.sh
