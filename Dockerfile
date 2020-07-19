FROM ubuntu:latest

ENV LANG=C.UTF-8 LC_ALL=C.UTF-8 LANGUAGE=C.UTF-8
ENV PATH /opt/conda/bin:$PATH

ENV PATH /usr/local/nvidia/bin/:$PATH
ENV LD_LIBRARY_PATH /usr/local/nvidia/lib:/usr/local/nvidia/lib64
# Tell nvidia-docker the driver spec that we need as well as to
# use all available devices, which are mounted at /usr/local/nvidia.
# The LABEL supports an older version of nvidia-docker, the env
# variables a newer one.
ENV NVIDIA_VISIBLE_DEVICES all
ENV NVIDIA_DRIVER_CAPABILITIES compute,utility
LABEL com.nvidia.volumes.needed="nvidia_driver"
ARG DEBIAN_FRONTEND=noninteractive

# Install base packages.
RUN apt-get update --fix-missing && apt-get install -y \
    bzip2 \
    ca-certificates \
    curl \
    gcc \
    git \
    libc-dev \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    wget \
    unzip \
    libevent-dev \
    build-essential && \
    rm -rf /var/lib/apt/lists/*

RUN wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh && \
    /bin/bash ~/miniconda.sh -b -p /opt/conda && \
    rm ~/miniconda.sh && \
    ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh && \
    echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc

# entity_api env
ADD entity_api /entity_api
RUN /opt/conda/bin/conda env create -f /entity_api/aida_entity.yml

# relation env
ADD ./relation /relation
# relation coarse env
RUN /opt/conda/bin/conda create -n aida_relation_coarse python=3.6 && \
    /opt/conda/envs/aida_relation_coarse/bin/pip install torch==0.4.1 && \
    /opt/conda/envs/aida_relation_coarse/bin/pip install gensim networkx spacy flask && \
    /opt/conda/envs/aida_relation_coarse/bin/python -m spacy download en_core_web_sm
# relation udp env
RUN /opt/conda/bin/conda create -n py27 python=2.7 && \
    /opt/conda/envs/py27/bin/pip install torch==0.4.1 && \
    /opt/conda/envs/py27/bin/pip install -r /relation/udp_requirements.txt
#    /opt/conda/envs/py27/bin/pip install pathlib==1.0.1
#    /opt/conda/envs/py27/bin/pip install numpy==1.16.2 scipy==1.2.1 gensim==3.5.0 pathlib==1.0.1 enum34==1.1.2
# relation fine-grained
RUN /opt/conda/bin/conda create -n py36 python=3.6 && \
    /opt/conda/envs/py36/bin/pip install torch==1.0.1 && \
    /opt/conda/envs/py36/bin/pip install -r /relation/aida_requirements.txt && \
    /opt/conda/envs/py36/bin/pip install langdetect rdflib pymystem3 flashtext jieba
RUN /opt/conda/envs/py36/bin/python -m nltk.downloader popular -d /opt/conda/envs/py36/share/nltk_data

# ru_event
RUN /opt/conda/bin/conda create -n ru_event python=3.5 && \
    /opt/conda/envs/ru_event/bin/pip install torch==0.3.1 && \
    /opt/conda/envs/ru_event/bin/pip install numpy flask sklearn tensorflow==1.0.0
ADD ./ru_event /ru_event

# preprocessing
ADD ./preprocessing /preprocessing

ADD ./entity /entity
ADD ./event /event
ADD ./aida_utilities /aida_utilities


ADD ./postprocessing /postprocessing
RUN cd /postprocessing/AIDA-Interchange-Format-master/python && \
    /opt/conda/envs/py36/bin/python setup.py install

RUN cd /postprocessing/ELMoForManyLangs && \
    /opt/conda/envs/aida_entity/bin/python setup.py install
RUN /opt/conda/envs/aida_entity/bin/pip install rdflib ujson
RUN cd /postprocessing/AIDA-Interchange-Format-master/python && \
    /opt/conda/envs/aida_entity/bin/python setup.py install

RUN /opt/conda/bin/conda clean -tipsy

LABEL maintainer="hengji@illinois.edu"

CMD ["/bin/bash"]