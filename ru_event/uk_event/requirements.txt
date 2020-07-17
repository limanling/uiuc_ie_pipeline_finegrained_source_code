wget --quiet https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda.sh

/bin/bash ~/miniconda.sh -b -p /opt/conda

rm ~/miniconda.sh

ln -s /opt/conda/etc/profile.d/conda.sh /etc/profile.d/conda.sh

echo ". /opt/conda/etc/profile.d/conda.sh" >> ~/.bashrc

conda create -n ru_event python=3.5 

conda activate ru_event

conda install pytorch=0.3 -c pytorch

pip install packages.txt