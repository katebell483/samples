import os
import random 
import string
import mimetypes
import sys
from PIL import Image, ImageSequence
from sklearn.preprocessing import LabelEncoder
from random import randint
from keras.utils import np_utils
from urllib.request import urlopen, urlretrieve

from .InvalidUsage import InvalidUsage

module_path = os.path.abspath(os.path.join('vision'))
if module_path not in sys.path:
    sys.path.append(module_path)
from vision.VisionPreprocess import VisionPreprocess

class VisionUtils():

    def __init__(self):
        # make the path be one directory higher
        self.path = os.path.abspath(os.path.join('vision'))
        self.tmp_dir = self.path + "/tmp/"
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def encode_labels(self, labels, num_categories):
        # encode class values as integers
        encoder = LabelEncoder()
        encoder.fit(labels)
        encoded_labels = encoder.transform(labels)

        # convert to one hot labels and return
        return np_utils.to_categorical(encoded_labels, num_categories)

    def map_label(self, prediction_int, labels_path):
        labels_array = []
        with open(labels_path,'r') as f:
            labels_array = [line.split(":")[0].strip() for line in f]
        sorted_labels_array = sorted(labels_array, key=str.lower)
        return sorted_labels_array[prediction_int]

    def download_still(self, url, gif_id):

        # validate url + get extension
        try:
            media_info = urlopen(url).info()
            content_type = media_info["Content-Type"]
            extension = mimetypes.guess_extension(content_type)
        except:
            raise InvalidUsage('Bad Request - Invalid Media', status_code=400)

        # default extenstion is jpg
        extension = ".jpg" if extension is None else extension        

        # set filepaths -- data_dir/<gif_id>.gif/jpg
        orig_path = "%s%s%s" % (self.tmp_dir, gif_id, extension)
        jpg_path =  "%s.jpg" % orig_path.split('.')[0]

        # get img from url and store as original type
        response = urlretrieve(url, orig_path)

        # convert orig to jpg
        Image.open(orig_path).convert('RGB').save(jpg_path)

        #clean up
        if(orig_path != jpg_path): 
            os.remove(orig_path)

        return jpg_path

    def download_sample_frame(self, gif_id, sample_location):

        # get all frames from gif
        url = "https://media4.img.com/media/%s/img.gif" % (gif_id)
        frames = self._download_all_frames(url, gif_id);

        # return a frame from the specified location
        num_frames = len(frames)
        sample_idx = int(num_frames * sample_location)
        return frames[sample_idx]

    def download_all_frames(self, url, gif_id):

        # validate url + get extension
        try:
            media_info = urlopen(url).info()
            content_type = media_info["Content-Type"]
            extension = mimetypes.guess_extension(content_type)
        except:
            raise InvalidUsage('Bad Request - Invalid Media', status_code=400)

        # store extracted frames in array
        filenames = []

        # download img and store in tmp directory
        tmp_gif_path = self.tmp_dir + gif_id + extension

        # save each frame from the gif
        try:
            urlretrieve(url, tmp_gif_path)

            # open gif, extract frames + store into tmp dir
            gif = Image.open(tmp_gif_path)

            index = 0
            for frame in ImageSequence.Iterator(gif):
                filename = "%s%s-%s.png" % (self.tmp_dir, gif_id, index)
                frame.save(filename)
                filenames.append(filename)
                index = index + 1

        except EOFError:
            logging.error("script failed to extract frames from gif with id %s \n" % gif_id)

        finally:
            os.remove(tmp_gif_path)

        return filenames

    def remove_tmp_files(self,imgs):
        for img in imgs:
            try:
                os.remove(img)
            except OSError:
                pass

    def get_tmp_id(self, N):
        return ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(N))

