FROM iontorrent/tsbuild

RUN apt-get update && \
    apt-get install -y curl
RUN git config --global http.sslVerify false
RUN cd /src && git clone https://github.com/iontorrent/TS.git
RUN cd /src/TS || true && MODULES='Analysis' ./buildTools/build.sh || true
