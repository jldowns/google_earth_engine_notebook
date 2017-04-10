
import os
import random
import wget
import datetime
import zipfile
import ee


def unzipURL(img_url):
    """ Downloads and unzips a file. Returns the path where everything is unzipped. """
    TMP_DIR="./tmp/"+str(random.randrange(999999))
    zip_filename = os.path.join(TMP_DIR, 'zipped_tile.zip')

    # make tmp directory
    if not os.path.exists(TMP_DIR):
        os.makedirs(TMP_DIR)

    # and delete everything in it:
    filelist = [ f for f in os.listdir(TMP_DIR)]
    for f in filelist:
        os.remove(os.path.join(TMP_DIR, f))


    # try:
    #     r = requests.get("https://earthengine.googleapis.com/api/download?docid=d32ed4c9201c7b3d2250bbf11f46ebf9&token=7ec22db241c2fd4c80622c531e7bef3c")
    #     print(r.status_code)
    #     # prints the int of the status code. Find more at httpstatusrappers.com :)
    # except requests.ConnectionError:
    #     print("failed to connect")
    #
    # z = zipfile.ZipFile(StringIO.StringIO(r.content))
    z.extractall()

    wget.download(img_url, zip_filename)
    zip_ref = zipfile.ZipFile(zip_filename, 'r')
    zip_ref.extractall(TMP_DIR)
    zip_ref.close()

    return TMP_DIR

    return

def element_to_img(geElement, resolution, bands, bounds):
    """
    Converts a google earth engine Element object (an element of an Image Collection)
    into a numpy array that you can display.

    bands: ['10', '20', '30']
    """

    DEFAULT_MAP_NAME = 'map_section'

    # create the Google Earth Engine Image object
    gee_img = ee.Image(geElement)

    # convert the simple list of band names into the dictionary that the query needs
    band_query_dict = [{'id': b} for b in bands]

    # get the download link from google
    path=gee_img.getDownloadUrl({
            'name': DEFAULT_MAP_NAME,  # name the file (otherwise it will be a uninterpretable hash)
            'scale': resolution,  # resolution in meters
            'crs': 'EPSG:4326', #4326                         #  projection
            'bands': band_query_dict,
            'region': str(bounds.getInfo()['coordinates'])
            });

    # debug output
    print path

    # convert to tiff
    tif_location = unzipURL(path)

    # get handles to the tiff files
    tif_filenames = [DEFAULT_MAP_NAME+'.'+b+'.tif' for b in bands]
    tif_paths = [os.path.join(tif_location, tf) for tf in tif_filenames]

    return tif_paths







def img_at_region(geCollection, resolution, band, geo_bounds):
    """
    Converts a google earth engine Element object (an element of an Image Collection)
    into a numpy array that you can display.

    bands: ['10', '20', '30]
    """

    DEFAULT_MAP_NAME = 'map_section'

    # create the Google Earth Engine Image object
    gee_img = geCollection.mosaic()

    # convert the simple list of band names into the dictionary that the query needs

    # get the download link from google
    path=gee_img.getDownloadUrl({
            'name': DEFAULT_MAP_NAME,  # name the file (otherwise it will be a uninterpretable hash)
            'scale': resolution,                              # resolution in meters
            'crs': 'EPSG:4326', #4326                         #  projection
            'bands': [{'id': 'R'}],
            'region': geo_bounds.getInfo()['coordinates']
            });

    # debug output
    print path

    # convert to tiff
    tif_location = unzipURL(path)

    # get handles to the tiff files
    tif_filenames = [DEFAULT_MAP_NAME+'.'+b+'.tif' for b in bands]
    tif_paths = [os.path.join(tif_location, tf) for tf in tif_filenames]

    return tif_paths




def available_bands(image_collection):
    band_ids = [band_info['id']
                for band_info
                in image_collection.first().getInfo()['bands']]
    return band_ids


def date_range(image_collection):
    time_format = '%Y-%m-%d'
    min_time = image_collection.aggregate_min('system:time_start').getInfo()
    max_time = image_collection.aggregate_max('system:time_end').getInfo()

    return {
        'begin_time': datetime.datetime.fromtimestamp(min_time/1000).strftime(time_format),
        'end_time': datetime.datetime.fromtimestamp(max_time/1000).strftime(time_format)
    }

def collection_length(image_collection):
    return image_collection.size().getInfo()

def all_images_at_location(image_collection, coordinates):
    """
    coordinates: (lat, long)
    """
    point = ee.Geometry.Point(coordinates)
    return image_collection.filterBounds(point)

def bound_geometry(corner1, corner2):
    """ Given 2 points, returns a Geometry object that represents the square
    those 2 points make up. """

    x1, y1 = corner1
    x2, y2 = corner2

    return ee.Algorithms.GeometryConstructors.LinearRing([[x1,y1],[x1,y2],[x2,y2],[x2,y1], [x1,y1]])


def bound_string(corner1, corner2):
    """
    Returns a string representation of the square defined by the 2 corners.
    """
    ulx, uly = corner1
    lrx, lry = corner2

    region =  [ulx,lry], [ulx, uly], [lrx, uly], [lrx, lry]  #h11v08
    return str(list(region))
