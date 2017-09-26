import os
import argparse
import cv2
import logging
import json
import numpy as np
import tensorflow as tf

from gevent import spawn, joinall
from keras.models import model_from_json
from keras.preprocessing import image
from keras.applications.vgg16 import preprocess_input

from vision.utils.YahooNsfw import YahooNsfw
from vision.VisionPreprocess import VisionPreprocess
from vision.VisionModels import VisionModels
from vision.utils.VisionUtils import VisionUtils
from vision.utils.InvalidUsage import InvalidUsage

os.environ["CUDA_DEVICE_ORDER"] = "PCI_BUS_ID"
os.environ["CUDA_VISIBLE_DEVICES"] = ""

"""
AWS related info removed
"""
class VisionApi():

    def __init__(self):
        self.module_path = '/mnt/ds/imgds'
        self.tmp_dir = self.module_path + "/vision/tmp/"
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)

    def test_nsfw_gif(self, gif_id, extract_frames, threshold):

        # if we're just testing first frame use img_s.gif, otherwise use downsampled version
        extension = "200_d.gif" if extract_frames else "img_s.gif"
        url = "https://media4.img.com/media/%s/%s" % (gif_id, extension)

        # get test frame/frames
        utils = VisionUtils()
        frames = utils.download_all_frames(url, gif_id) if extract_frames else [utils.download_still(url, gif_id)]

        # instantiate new yahoo nsfw class
        yahoo = YahooNsfw()

        # spawn a thread per frame
        results = []
        threads = [spawn(yahoo.get_probability, frame) for frame in frames]

        # call yahoo asychronously and gather results
        joinall(threads)
        for thread in threads:
            if thread.value:
                results.append(thread.value)
                # as soon as we cross nsfw threshold return
                if thread.value > threshold: break

        # get highest_probability returned
        highest_probability = max(results)

        # clean up tmp media files
        utils.remove_tmp_files(frames)

        return self._build_binary_response("is_nsfw", float(highest_probability), threshold)

    def test_cartoon_gif(self, gif_id, threshold):

        # build media url from gif_id
        url = "https://media4.img.com/media/%s/img_s.gif" % (gif_id)

        # download image
        utils = VisionUtils()
        img_path = utils.download_still(url, gif_id)

        # get model either stored locally or on s3
        models = VisionModels()
        model = models.get_model("cartoon")

        # run image through model for prediction
        pred_data = self._get_prediction([img_path], model)

        # extract float prediction
        pred_float = float(pred_data[0][0])

        # model trained with non-cartoon as 1 and cartoon as 0, so needs to be switched
        prediction = 1.0 - pred_float

        return self._build_binary_response("is_cartoon", prediction, threshold)

    def test_celeb_gif(self, gif_id, threshold):

        # get all frames from gif
        utils = VisionUtils()
        url = "https://media4.img.com/media/%s/img.gif" % (gif_id)
        frames = utils.download_all_frames(url, gif_id);

        # get all faces in the GIF
        try:
            faces = self._get_all_faces(frames)
        except:
            raise InvalidUsage('Error extracting facial information', status_code=500)
        finally:
            # clean up
            utils.remove_tmp_files(frames)

        # validate returned image
        if all(face is None for face in faces):
            raise InvalidUsage('Bad Request - Valid face not found', status_code=400)
       
        # remove Nones
        faces = [face for face in faces if face is not None]

        # save face to original path
        paths = []
        for i, face in enumerate(faces):
            img_path = self.tmp_dir + gif_id + "-" + str(i) + ".jpg"
            cv2.imwrite(img_path, face)
            paths.append(img_path)
        
        models = VisionModels()
        model = models.get_model("celeb")

        # run image through model for prediction
        pred_datas = self._get_prediction(paths, model)

        # get the most likely labels for each face
        results = []
        for pred_data in pred_datas:
            pred_np_int = np.argmax(pred_data[0])
            confidence = float(pred_data[0][pred_np_int])

            # convert int label to string
            labels_path = self.module_path + "/vision/data/celeb/data_labels.txt"

            utils = VisionUtils()
            prediction = utils.map_label(int(pred_np_int), labels_path)

            results.append((confidence, prediction))

        # clean up
        tmp_paths = frames + [img_path]
        utils.remove_tmp_files(tmp_paths)

        return self._build_multi_response("celeb", results, threshold)

    def preprocess_face_image(self, media_url, gif_id, sq_img_dim):
        
        # init utils lib
        utils = VisionUtils()

        # if gif, get all frames
        if gif_id:
            media_url = "https://media4.img.com/media/%s/img.gif" % (gif_id)
            frames = utils.download_all_frames(media_url, gif_id);
        else:
            gif_id = utils.get_tmp_id(10)
            frames = [utils.download_still(media_url, gif_id)]

        # extract + align face using CMU opeface lib
        try:
            face = self._get_single_face(frames)
        except:
            raise InvalidUsage('Error extracting facial information', status_code=500)
        finally:
            # clean up
            utils.remove_tmp_files(frames)

        # validate returned image
        if face is None:
            raise InvalidUsage('Bad Request - Valid face not found', status_code=400)

        # save face
        img_path = self.tmp_dir + gif_id + "-face.jpg"
        cv2.imwrite(img_path, face)

        # clean up
        utils.remove_tmp_files(frames)

        # return file
        return img_path

    def _get_single_face(self, frames):
        max_steps = 10
        step = int(len(frames) / max_steps)
        step = 1 if step < 1 else step

        preprocess = VisionPreprocess() 

        #sample gif every 10 frames to look for face
        for i in range(0,len(frames), step):

            # convert to np array
            img_path = frames[i]
            np_img = cv2.imread(img_path)        

            # get face
            face = preprocess.get_aligned_face(np_img, 224, None)

            # as soon as face found return
            if face is not None:
                break

        return face
    
    def _get_all_faces(self, frames):
        max_steps = 10
        step = int(len(frames) / max_steps)
        step = 1 if step < 1 else step

        preprocess = VisionPreprocess() 
       
        #sample gif every 10 frames to look for face
        for i in range(0,len(frames), step):

            # convert to np array
            img_path = frames[i]
            np_img = cv2.imread(img_path)        

            # get bounding boxs
            bbs = preprocess.get_all_bounding_boxes(np_img)
            faces = [preprocess.get_aligned_face(np_img, 224, bb) for bb in bbs]

            # return first valid face/s
            if not all(face is None for face in faces):
                return faces
        return faces

    # TODO: put in Models file + use preprocessing class
    def _get_prediction(self, img_paths, model):
        preprocess = VisionPreprocess()
        # make prediction using cpu
        with tf.device('/cpu:0'):
            predictions = []
            for path in img_paths:
               img = image.load_img(path, target_size=(224, 224))
               x = image.img_to_array(img)
               x = np.expand_dims(x, axis=0)
               x = preprocess_input(x)
               predictions.append(model.predict(x)) 
        # clean up
        utils = VisionUtils()
        utils.remove_tmp_files(img_paths)

        return predictions
    
    def _build_multi_response(self, model_name, results, threshold):
        
        # prep response
        data = {}
        data["predictions"] = []
       
        for confidence, prediction in results:
            # only return results when above treshold
            if confidence < threshold:
                prediction = "Unknown"
                confidence = "NA"
            
            result = {}
            result[model_name] = prediction
            result["confidence"] = confidence
            data["predictions"].append(result)

        # convert to json and return
        return json.dumps(data)

    def _build_binary_response(self, test_label, prediction, threshold):
        # prep response
        data = {}
        data["probabilities"] = {}
        data["probabilities"][test_label] = prediction > threshold
        data["probabilities"]["result"] = prediction

        # convert to json and return
        return json.dumps(data)

 
