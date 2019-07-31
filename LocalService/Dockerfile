From nvidia/cuda:10.0-cudnn7-runtime-ubuntu16.04

ENV LANG C.UTF-8
COPY sources.list /etc/apt/

ARG UID=10
ARG GID=10

# python3
RUN apt-get update \
    && sh -c '/bin/echo -e "Y" | apt-get install software-properties-common python-software-properties'  \
    && sh -c '/bin/echo -e "\n" | add-apt-repository ppa:deadsnakes/ppa' \
    && apt-get update \
    && sh -c '/bin/echo -e "Y" | apt-get install python3.6' \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.5 1 \
    && update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.6 2 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python2 100 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3 150 \
    && sh -c '/bin/echo -e "Y" | apt-get install python3-pip' \
    && python -m pip install --upgrade pip \
    && groupadd -g ${GID:= $GID} fq \
    && useradd -m -s /bin/bash -u ${UID:= $UID} -g $GID gpudashboard 

WORKDIR /home/gpudashboard
ADD ./localapp .
RUN apt-get install -y python3.6-dev \
    && pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt \
    && python setup.py install

CMD ["python","app_start.py"]
