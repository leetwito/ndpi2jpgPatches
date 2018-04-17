
from suds.client import Client
import urllib
from suds.plugin import MessagePlugin
import os

'''
                # build the url to get the image snapshot
                # parameters:
                # pathOrUid: the path of the image we want to retrieve
                # timeframe: the index of the timeframe we wish to load. Usually 0, unless we are dealing with images that contain time series.
                # layer: the index of the layer we wish to load. Usually 0, unless we are dealing with images that Z-stacks.
                # x: the top left pixel x coordinate of the image at which we want the snapshot to start at. This value is expressed in base level scale.
                # y: the top left pixel y coordinate of the image at which we want the snapshot to start at. This value is expressed in base level scale.
                # width: the width of the image we want to read. This value is expressed in base level scale.
                # height: the height of the image we want to read. This value is expressed in base level scale.
                # scale: the factor by which we want the width and height parameters to be scaled by. The resulting image will be width * scale pixels wide and height * scale pixels tall

'''
class LogPlugin(MessagePlugin):
    def sending(self, context):
        print(str(context.envelope))
    def received(self, context):
        print(str(context.reply))

def getPatchWidthHeight(tot_width, tot_height, N_PATCHES):
    '''
    calculate patch dimensions.
    take biggest patch size so that N_PATCHES*patch_size will be smaller than image size
    '''
    patch_width = int(1.0*tot_width / N_PATCHES)
    patch_height = int(1.0*tot_height / N_PATCHES)
    print('org size: {}x{}\npatch size: {}x{}'.format(tot_width, tot_height, patch_width, patch_height))
    # right_pixels_removed = tot_width - patch_width*N_PATCHES
    # bottom_pixels_removed = tot_height - patch_height*N_PATCHES
    # print('{0} pixels were removed from right side ({1:.2f}% patch width)'.format(right_pixels_removed, 100.0*right_pixels_removed/patch_width))
    # print('{0} pixels were removed from bottom side ({1:.2f}% patch height)'.format(bottom_pixels_removed, 100.0*bottom_pixels_removed/patch_height))
    return patch_width, patch_height

def getTopLeftPixelForPatch(row, col, patch_width, patch_height):
    x = col * patch_width
    y = row * patch_height
    return x, y

FILES_PATH = "C:/Users/Lee Twito/PycharmProjects/patho1/pathology_imgs/ndpi_imgs"
N_PATCHES = 10 # will split image into NxN patches
# scales = np.arange(1.0, 0.1, -0.05)
scales = [1.0]

client = Client("http://localhost:54001/API?singleWsdl") # , plugins=[LogPlugin()]
client.set_options(cache=None)
files = client.service.GetFiles(path=FILES_PATH)

for scale in scales:
    for i, filename in enumerate(files[0]):
        print ('scale {} , image - {}'.format(scale, os.path.basename(filename)))
        info = client.service.GetImageInfo(filename)
        tot_width = info.Width
        tot_height = info.Height
        patch_width, patch_height = getPatchWidthHeight(tot_width, tot_height, N_PATCHES)
        for row in range(N_PATCHES):
            for col in range(N_PATCHES):
                x, y = getTopLeftPixelForPatch(row, col, patch_width, patch_height) # x,y are like openCV coordinates

                parameters = {'pathOrUid': filename, 'timeframe': 0, 'layer': 0, 'x': x, 'y': y, 'width': patch_width, 'height': patch_height,
                              'scale': scale}
                url = "http://localhost:54001/region?" + urllib.urlencode(parameters)

                file_base_name = filename.split('/')[-1][:-5]
                directory = os.path.dirname(FILES_PATH) + "/snapshots/{0}-patch{1}x{2}".format(file_base_name, patch_width, patch_height)
                if not os.path.exists(directory):
                    os.makedirs(directory)
                urllib.urlretrieve(url, directory + "{0}-r{1}c{2}/{0}-r{1}c{2}.png".format(file_base_name, row, col)) # save it locally

                # find the appropriate scale but also maintain aspect ratio. take 1000 pixels maximum in one of the dims
                # if (width >= height):
                #     scale = 1000. / width
                # else:
                #     scale = 1000. / height