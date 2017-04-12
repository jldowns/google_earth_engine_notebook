WORK_DIR=`pwd`/notebook
CREDENTIALS_DIR=`pwd`/credentials
IMAGE_NAME=npsvisionlab/opencv-notebook
# IMAGE_NAME=jldowns/google_earth_engine_notebook

docker run -it --rm \
    -p 8889:8888 \
    -v "$PWD/notebooks":/notebooks \
    $IMAGE_NAME
#
# docker run -it --rm \
#     -p 8888:8888 \
#     -v $WORK_DIR:/home/jovyan/work \
#     -v $CREDENTIALS_DIR:/home/jovyan/.config/earthengine \
#     -e GRANT_SUDO=yes --user root \
#     $IMAGE_NAME \
#     start-notebook.sh --NotebookApp.token=''
