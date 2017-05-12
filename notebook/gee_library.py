
import os
import random
import datetime
import zipfile
import ee
import matplotlib.image as mpimg
import requests, StringIO
import tifffile as tiff



class ServerError(Exception):
    """
    This exception communicates that a request to Google's severs returned
    a bad response. Use it like:

    raise ServerError("Got a 404 resposnse.")
    """
    pass



def unzipURL(img_url, tmp_directory = None):
    """
    Downloads and unzips a file in a tmp directory.
    Hits the server once.

    img_url: A web address to a zip file.
    tmp_directory: Optional path to unzip the contents.

    Returns: Path to the directory containing the contents of the zip file.
    """

    #
    # Set up temp directory
    #
    if tmp_directory == None:
        tmp_directory="./tmp/"+str(random.randrange(99999999))
    zip_filename = os.path.join(tmp_directory, 'zipped_tile.zip')
    # make tmp directory
    if not os.path.exists(tmp_directory):
        os.makedirs(tmp_directory)
    # and delete everything in it:
    filelist = [ f for f in os.listdir(tmp_directory)]
    for f in filelist:
        os.remove(os.path.join(tmp_directory, f))

    #
    # Download file
    #
    try:
        r = requests.get(img_url)
        sc = r.status_code
    except requests.ConnectionError as e:
        raise e

    if r.status_code == 200:
        z = zipfile.ZipFile(StringIO.StringIO(r.content))
        z.extractall(tmp_directory)
        z.close()
        return tmp_directory
    elif r.status_code == 400:
        print "Uh-oh. Status code 400 (Bad Request). Possible problems:"
        print "- You requested a band that wasn't available in every image."
        print "- Some other unknown issue."
        raise ServerError("Status code 400")
    elif r.status_code == 429:
        raise ServerError("Status code 429")
    else:
        raise ServerError("Uh-oh. Status code " + str(r.status_code))

    # Fall through on handled error/exception
    raise Exception("Unknown error in unzipURL().")



def estimate_image_size_at_resolution(bounds_geometry, resolution):
    """
    Estimates the resulting image dimentions at a specific resolution.
    This function is useful to use before trying to download a patch of earth
    imagery to make sure you're not trying to download a 300 MB image or something.
    (Right now this is very rough and not 100 percent accurate. But it does
    get in the ballpark.)

    Hits the server twice.

    bounds_geometry: gee.Geometry object
    Resolution: meters per pixel

    Returns: {'height': estimated image height, 'width': estimated image width}
    """

    coords = bounds_geometry.getInfo()['coordinates'][0]


    xs = [x for [x,y] in coords]
    ys = [y for [x,y] in coords]

    top_left = min(xs), max(ys)
    bottom_left = min(xs), min(ys)
    bottom_right = max(xs), min(ys)

    height = ee.Geometry.Point(top_left).distance(ee.Geometry.Point(bottom_left)).getInfo() / resolution
    width = ee.Geometry.Point(bottom_left).distance(ee.Geometry.Point(bottom_right)).getInfo() / resolution

    return {
        'height': height,
        'width': width }



def img_at_region(geCollection, resolution, bands, geo_bounds, verbose=False):
    """
    High-level function for retreiving imagery from Google Earth Engine.
    img_at_region() returns a dictionary of numpy arrays based on the images
    retreived by tif_at_region().

    geCollection: ee.ImageCollection object.
    resolution: Image resolution in meters per pixel
    bands: List of requested bands. For example, ['R', 'G', 'B']
    geo_bounds: ee.Geometry object representing the area on the earth to get
        the imagery from.
    verbose: Set to True to print out debugging information.

    Returns a dictionary whose values are numpy arrays and whose keys are
    band names. For example:
    { 'R': numpy_img, 'G': numpy_img}
    """
    tif_band_dictionary = tif_at_region(geCollection, resolution, bands, geo_bounds, verbose)
    img_band_dictionary = {}

    for k,v in tif_band_dictionary.items():
        # img_band_dictionary[k] = mpimg.imread(v)
        img_band_dictionary[k] = tiff.imread(v)

    return img_band_dictionary


def tif_at_region(geCollection, resolution, bands, geo_bounds, verbose=False):
    """
    Downloads imagery in `bands` from the area encompassed by `geo_bounds`.

    geCollection: ee.ImageCollection object.
    resolution: Image resolution in meters per pixel
    bands: List of requested bands. For example, ['R', 'G', 'B']
    geo_bounds: ee.Geometry object representing the area on the earth to get
        the imagery from.
    verbose: Set to True to print out debugging information.

    Hits the server thrice.
        - Once for geo_bounds.getInfo()['coordinates']
        - Once for getDownloadUrl()
        - Once for downloading the zip

    Returns a dictionary mapping band names to tiff image paths. For example:
        {'10': './tmp/APFR/map_section.10.tif',
         '20': './tmp/APFR/map_section.20.tif',
         '30': './tmp/APFR/map_section.30.tif' }
    """

    DEFAULT_MAP_NAME = 'map_section'

    # create the Google Earth Engine Image object
    gee_img = geCollection.filterBounds(geo_bounds).select(bands).mosaic()

    # convert the simple list of band names into the dictionary that the query needs
    bands_string = [{'id': b} for b in bands]

    # get the download link from google
    path=gee_img.getDownloadUrl({
            'name': DEFAULT_MAP_NAME,  # name the file (otherwise it will be a uninterpretable hash)
            'scale': resolution,                              # resolution in meters
            'crs': 'EPSG:4326', #4326                         #  projection
            'bands': bands_string,
            'region': geo_bounds.getInfo()['coordinates']
            });

    # debug output
    if verbose:
        print path

    # unzip the tiff
    tif_location = unzipURL(path)

    tif_filename_object = {}
    for b in bands:
        # each tif in the zip file is in the format 'mapname.band.tif'
        tif_filename = DEFAULT_MAP_NAME+'.'+b+'.tif'
        tif_path = os.path.join(tif_location, tif_filename)
        # add the calculated tif path to a dictionary, keyed by the band name
        tif_filename_object[b] = tif_path



    return tif_filename_object

def dates_available(geCollection):
    """
    Returns a list of the dates available for this collection.

    geCollection: ee.ImageCollection object

    Returns a list of date strings in YYYY-MM-DD format.
    """

    timestamps =  geCollection.aggregate_array('system:time_start').getInfo()
    dateformat_array = [timestamp_to_datetime(t) for t in timestamps]

    return  dateformat_array


def available_bands(image_collection):
    """
    Determines which bands are available in the image collection.
    Since the images in a specific collection are not guarenteeded to all
    share the same bands, this function looks at the bands in the first image, and
    then calculates how many images in the collection include that band.
    Since the band names are determined from a single image, the bands that
    are returned may only be a subset of all the bands present in a collection.
    However, this function is helpful to at least determine the naming scheme
    used in a collecion, and whether it is safe to assume that certain bands
    are included in every image in the collection.

    image_collection: ee.ImageCollection object

    Hits the server 1+number_of_bands times

    Returns a dictionary in format
    { "band1": { "number_available" : number of images that contain band1,
                 "percent_available" : percent of all images in collection that contain band1 }
                },
      "band2": {...
    }
    """
    band_ids = [band_info['id']
                for band_info
                in image_collection.first().getInfo()['bands']]

    collection_size = image_collection.size().getInfo()

    availability_dict = {}
    for b in band_ids:
        imgs_available = image_collection.select(b).size().getInfo()
        percent_available = imgs_available/collection_size*100
        availability_dict[b] = {
            "number_available": imgs_available,
            "percent_available": percent_available
        }
        # print "'"+b+"' available in "+ str(imgs_available) + " images. ("+str(percent_available)+"%)"

    return availability_dict


def date_slices(geImageCollection, bounds_geometry, descending=False):
    """
    Returns a list of non-overlapping date ranges where every date range
    covers the bounds_geometry.
    This function is not very efficient takes a loong time.
    """

    date_slices = []
    date_list = list(set(dates_available(geImageCollection)))
    date_list.sort()
    print len(date_list), "unique dates found."
    # convert these strings into Date objects
    date_list = [ee.Date(d) for d in date_list]
    start_date = date_list[0]

    for i in range(len(date_list)):
        # We're using an integer iterator because we want some lookahead later on
        end_date = date_list[i].advance(1, 'day')
        potential_slice_collection = geImageCollection.filter(ee.Filter.date(start_date, end_date))

        # If this date slice covers the image 100%, add it to the date_slices list
        # and increment the start date to the next available date
        if collection_fills_bounds(potential_slice_collection, bounds_geometry):
            date_slices.append((start_date, end_date))
            try:
                start_date = date_list[i+1]
            except IndexError:
                pass

        print i

    return date_slices



def timestamp_to_datetime(timestamp, time_format = '%Y-%m-%d'):
    """
    Converts the UNIX epoch timestamp used by the Earth Engine database into a
    format readable by humans (and also the format used by the Earth Engine
    date filters)

    timestamp: UNIX time epoch
    time_format: optional datetime format

    Returns a datetime string.
    """
    return datetime.datetime.fromtimestamp(timestamp/1000).strftime(time_format)


def date_range(image_collection):
    """
    Determines the date range of the images included in an image collection.

    image_collection: ee.ImageCollection object

    Returns a dictionary in the format:
    { 'begin_time': '2009-01-03',
      'end_time'  : '2012-10-21' }
    """
    time_format = '%Y-%m-%d'
    min_time = image_collection.aggregate_min('system:time_start').getInfo()
    max_time = image_collection.aggregate_max('system:time_end').getInfo()

    return {
        'begin_time': datetime.datetime.fromtimestamp(min_time/1000).strftime(time_format),
        'end_time': datetime.datetime.fromtimestamp(max_time/1000).strftime(time_format)
    }

def collection_length(image_collection):
    return image_collection.size().getInfo()

def bound_geometry(corner1, corner2):
    """
    Given 2 points, returns a Geometry object that represents the rectangle
    those 2 points make up. Note that the coordinates are provided in
    longitude, latitude order.

    corner1: (longitude, latitude)
    corner2: (longitude, latitude)

    Returns an ee.Geometry object.
    """

    x1, y1 = corner1
    x2, y2 = corner2

    # How important is this? I don't know.
    left_x,top_y     = min([x1, x2]), max([y1, y2])
    right_x,bottom_y = max([x1, x2]), min([y1, y2])

    xMin=min([x1, x2])
    yMin=min([y1, y2])
    xMax=max([x1, x2])
    yMax=max([y1, y2])

    # First create a "linear ring" that is the outline of the points.
    rectangle_representation = ee.Geometry.Rectangle([xMin, yMin, xMax, yMax])

    # then fill in this ring by calculating the convex hull
    return rectangle_representation


def square_centered_at(point, half_distance):
    """
    Returns a ee.Geometry object that is a square, centered at point,
    where each side measures 2 times half_distance. (half_distance can be
    thought of like a radius, since the function uses a circle to make the
    measurements.)

    Doesn't hit the server.

    point: (longitude, latitude)
    half_distance: in meters

    Returns an ee.Geometry object.
    """

    return ee.Geometry.Point(point).buffer(half_distance).bounds()

def collection_fills_bounds(geImageCollection, bounds_geometry):
    """
    Returns true if the images in geImageCollection have 100 percent coverage
    of the bounds_geometry.
    """
    collection_geometry = geImageCollection.geometry()
    bounded_collection = collection_geometry.intersection(bounds_geometry, 0.01)
    missing_spots = bounds_geometry.difference(bounded_collection, 0.01)
    return missing_spots.area().getInfo() == 0
