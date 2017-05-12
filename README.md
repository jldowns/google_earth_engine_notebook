# Google Earth Engine Notebook and Tutorial

Here's a little series of Jupyter Notebooks that walk through pulling imagery from Google Earth Engine. While GEE has many features and server-side computes available, this guide treats GEE simply as an imagery datastore and focuses on navigating the images by location and spectrum.

The second part of this guide (not finished yet) will use the imagery in conjunction with TensorFlow for some light machine learning.

At the end of these guides you should be able to request imagery by location, band, and date, and then use that imagery for machine learning.

*Tested on Docker 17.03, MacOS Sierra, Chrome*

## iPython Chapters

1. Introduction: *Getting imagery from GEE*
2. Spectrums: *Pulling data from different specra and collections.*
3. Supervised: *A gentle introduction to TensorFlow*
4. Unsupervised: *Using autoencoders and clustering to group images* -->

### Multispectrum Experiment
5. Data Acquisition
6. All-in-one Analysis
7. Pipelined Analysis

## Authenticating

Before you can use the Google Earth Engine, you must sign up with your Google account. You can sign up here: https://earthengine.google.com/ (While the website claims it could take a week to get an account, I've never seen it take more than 10 seconds.)

After you've created an account, navigate to the repository directory and review and run `./authenticate_gee.sh`. After following the prompts, a `credentials` file should appear in your `./credentials` directory. This file contains your authentication token. The scripts in this repo set that folder as a shared volume so that your credentials are saved across container restarts.

## Starting the Notebook

The Docker image used in this guide is based on the [TensorFlow Jupyter Stack](https://github.com/jupyter/docker-stacks/tree/master/tensorflow-notebook). The `start_gee_notebook.sh` script runs the following command:

```
docker run -it --rm \
    -p 8888:8888 \
    -v $WORK_DIR:/home/jovyan/work \
    -v $CREDENTIALS_DIR:/home/jovyan/.config/earthengine \
    -e GRANT_SUDO=yes --user root \
    jldowns/google_earth_engine_notebook:1.0 \
    start-notebook.sh --NotebookApp.token=''
```

This will run the container on your machine with root access and security tokens disabled, because it's more convenient when just running on a local machine. You can also just run this command without cloning this repo if you want a Google Earth Engine/TensorFlow Jupyter Notebook environment.

That command also creates two shared volumes: the first is the work directory, which is where the tutorials are kept. The second is a "credentials" directory, described earlier.

After starting the container, travel to localhost:8888 in your browser to access the notebooks.
