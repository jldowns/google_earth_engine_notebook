FROM jupyter/tensorflow-notebook

USER root

RUN apt-get update

# crypto dependencies
RUN apt-get install -y build-essential libssl-dev libffi-dev python-dev python-imaging-tk

# python packages
RUN pip2 install google-api-python-client pyCrypto 'pyOpenSSL>=0.11' earthengine-api tifffile wget tqdm
RUN pip2 install protobuf --upgrade
RUN conda install -y -c conda-forge nbstripout

# ensure we can run python2 binary commands
RUN export PATH=$PATH:/opt/conda/envs/python2/bin
