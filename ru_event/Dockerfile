FROM ubuntu:latest

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

RUN apt update && \
    apt upgrade -y && \
    apt install wget -y &&\
    apt clean && \
    rm -rf /var/lib/apt/lists/*

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc

RUN /opt/conda/bin/conda create -n ru_event python=3.5 && \
    /opt/conda/envs/ru_event/bin/pip install torch==0.3.1 && \
    /opt/conda/envs/ru_event/bin/pip install numpy flask sklearn tensorflow==1.0.0

ADD ./ru_event ./ru_event

CMD /bin/bash
