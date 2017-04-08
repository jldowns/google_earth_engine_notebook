WORK_DIR=`pwd`/notebook
CREDENTIALS_DIR=`pwd`/credentials

docker run -it --rm \
    -p 8888:8888 \
    -v $WORK_DIR:/home/jovyan/work \
    -v $CREDENTIALS_DIR:/home/jovyan/.config/earthengine \
    -e GRANT_SUDO=yes --user root \
    jldowns/google_earth_engine_notebook \
    start-notebook.sh --NotebookApp.token=''
