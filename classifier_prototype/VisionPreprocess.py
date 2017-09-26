import subprocess
import os
import sys
import numpy as np
import cv2

from keras.applications.vgg16 import preprocess_input

file_path = os.path.abspath(os.path.dirname('__file__'))
path_args = file_path.split('/')
project_root_idx = path_args.index('imgds') + 1
project_root_path = '/'.join(path_args[:project_root_idx])

if project_root_path not in sys.path:
    sys.path.append(project_root_path)

from vision.utils.InvalidUsage import InvalidUsage

openface_path = project_root_path + "/vision/libs/openface/openface"
if openface_path not in sys.path:
    sys.path.append(openface_path)
from align_dlib import AlignDlib

"""
TODO: 
- explain
- dont switch back and forth btw cv2 + PIL
- handle return false if more than one face
"""

class VisionPreprocess():

    def __init__(self):
        self.tmp_dir = project_root_path + '/vision/tmp/'
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        # get dlib face predictor 
        self.dlib_predictor_path = self.tmp_dir + "shape_predictor_68_face_landmarks.dat"
        if not os.path.isfile(self.dlib_predictor_path): 
            cmd = "curl -o %s.bz2 http://dlib.net/files/shape_predictor_68_face_landmarks.dat.bz2 && bzip2 -d %s.bz2" % (dlib_predictor_path, dlib_predictor_path)
            subprocess.run(cmd, shell=True, stderr=subprocess.DEVNULL)
    
    
    def get_aligned_face(self, np_img, sq_img_dim, bounding_box):
        openface = AlignDlib(self.dlib_predictor_path)
        aligned_img = openface.align(sq_img_dim, np_img, skipMulti=True, bb=bounding_box)
        return aligned_img

    def get_all_bounding_boxes(self, np_img):
        openface = AlignDlib(self.dlib_predictor_path)
        bbs = openface.getAllFaceBoundingBoxes(np_img)
        return bbs

    def preprocess_input_vgg(self, x):
            X = np.expand_dims(x, axis=0)
            X = preprocess_input(X)
            return X[0]
