CREDENTIALS_DIR=`pwd`/credentials

docker run -it \
    -v $CREDENTIALS_DIR:/home/jovyan/.config/earthengine \
    jldowns/google_earth_engine_notebook:1.1 \
    /opt/conda/envs/python2/bin/earthengine authenticate
