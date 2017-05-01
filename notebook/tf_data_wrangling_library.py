
# Math Stuff
import ee, scipy.misc, random, os, errno
from glob import glob
import numpy as np
from threading import Thread
from itertools import chain
from itertools import izip

# GEE stuff
from gee_library import *
ee.Initialize()

# debug stuff
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Multi threading libraries
import time
from threading import Thread

# Protobuffer imports
import tensorflow as tf
from scipy import misc

import random, string
from tqdm import tqdm



def batch_download(gps_bounds, destination_image_directory, count):
    """
    gps_bounds: list of gps coordinates. For example:
            [ ((-73.965, 40.614), (-73.920, 40.693)),
              ((-105.127, 39.569), (-104.890, 39.825)) ]


    """

    # Prepare by creating the directories if they don't exist
    try:
        os.makedirs(destination_image_directory)
    except OSError, e:
        if e.errno != errno.EEXIST:
            raise

    #
    # Download data
    #
    for i in range(len(train_gps_bounds)):
        print "downloading training class", i
        download_data(gps_bounds[i], count, destination_image_directory)



def create_label_csv_file(directory_list, label_filename, class_list=None, file_extensions=['png']):
    """
    Creates a CSV file called `label_filename` written in the following format:
        path_to_image, class_number
        path_to_image, class_number
        path_to_image, class_number
        ...

    directory_list: List of directories to search through. The directories
        will be searched recursively.
    label_filename: The filename (including extension) of the CSV file to be
        written to. If the file already exists, it will be overwritten.
    class_list: Optional list of labels (strings). All the images found in each
        directory in `directory_list[i]` will be assigned the class found at
        `class_list[i]`. `directory_list` and `class_list` must be the same length.
        If `class_list` is omitted, classes will be assigned the
        numbers 0 through len(directory_list)
    file_extensions: List of file extensions (strings) of the files to assign
        as examples.
    """

    if class_list == None:
        class_list = list(range(len(directory_list)))

    assert(len(directory_list) == len(class_list))

    # Open the label file for writing
    with open(label_filename, "w") as myfile:
        # Every directory_list item corresponds to a class_list item.
        for dir, klass in izip(directory_list, class_list):
            print "Class", klass, "..."
            for ext in file_extensions:
                # Find all the matching files
                found_files = (chain.from_iterable(glob(os.path.join(x[0], '*.'+ext)) for x in os.walk('.')))
                for filename in found_files:
                        myfile.write(filename + "," + str(klass) + "\n")






def convert_to_protobuf(proto_filename, label_file):
    print "Protobuffing", proto_filename
    # Open a protobuffer writer
    proto_writer = tf.python_io.TFRecordWriter(proto_filename)

    # Iterate over every exmaple and put it in the protobuffer
    for line in tqdm(open(label_file).read().splitlines()):
        png_path, label = line.split(',')
        img = misc.imread(png_path).flatten()

        proto_example = tf.train.Example(
            features=tf.train.Features( # a map of string to Feature proto objects
                feature={
                    # A Feature contains one of either a int64_list,
                    # float_list, or bytes_list
                    'label': tf.train.Feature(
                        int64_list=tf.train.Int64List(value=[int(label)])),
                    'image': tf.train.Feature(
                        int64_list=tf.train.Int64List(value=img.astype("int64")))
                }
            )
        )

        # use the proto object to serialize the example to a string
        serialized = proto_example.SerializeToString()
        # write the serialized object to disk
        proto_writer.write(serialized)







####################
# For Internal Use #
####################






def randomword(length):
    """
    Generates a random string of length `length`.
    """
    return ''.join(random.choice(string.lowercase) for i in range(length))

def save_random_tile_at(coords, meters, pixels, bands, file_name):
    try:
        # Get random tile in box
        ((longmin, latmin),(longmax, latmax)) = coords

        # get random coords
        longitude = random.uniform(longmin, longmax)
        latitude = random.uniform(latmin, latmax)

        # Calculate resolution
        resolution = meters/pixels

        # Build the GPS box Geometry object
        tile_bounds = square_centered_at(
            point = (longitude, latitude),
            half_distance = meters
        )

        # load image collection
        monterey_collection = ee.ImageCollection('USDA/NAIP/DOQQ')\
            .filterBounds(tile_bounds)

        # request imagery
        tiles = img_at_region(monterey_collection, resolution, bands, tile_bounds)

        # resize img to requested size
        np_band_array = [scipy.misc.imresize(tiles[b], (pixels, pixels)) for b in bands]

        # and stack the images in a matrix
        img = np.dstack(np_band_array)

        # Save image to file
        scipy.misc.toimage(img, cmin=0.0, cmax=-1).save(file_name)




    #
    # Error Handling
    #
    except ServerError as e:
        print e, file_name, coords
    except Exception as e:
        print e, file_name, coords
    return







def download_data(gps_bound_list, number_of_examples, directory, delay=3):
    """ Downloads random tiles from a list of regions to `directory`.
    Spawns a thread for each image with a delay of `delay` seconds
    between thread spawns. """

    if not os.path.exists(directory):
        os.makedirs(directory)

    for i in range(number_of_examples):
        if i%100 == 0:
            print i
        t = Thread(target=save_random_tile_at,
                   args=(random.choice(gps_bound_list), # we randomly choose from the boxes
                         200,
                         50,
                         ['R', 'G', 'B'],
                         os.path.join(directory, randomword(10)+'.png')))
        t.start()
        time.sleep(delay)
