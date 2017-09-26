import os
import sys
import numpy as np
import datetime
import boto3
from pathlib import Path
from keras.models import Model, model_from_json
from keras.layers import Dense, Flatten, Input, BatchNormalization, Activation
from keras.optimizers import SGD
from keras.applications.vgg16 import VGG16
from keras_vggface.vggface import VGGFace

"""
AWS INFO REMOVED
"""

file_path = os.path.abspath(os.path.dirname('__file__'))
path_args = file_path.split('/')
project_root_idx = path_args.index('imgds') + 1
project_root_path = '/'.join(path_args[:project_root_idx])

if project_root_path not in sys.path:
    sys.path.append(project_root_path)

class VisionModels():

    def __init__(self):
        self.final_model_dir = project_root_path + "/vision/models/final/"
        self.in_progress_model_dir = project_root_path + "/vision/models/in_progress/"

    def build_new_facial_recognition_model(self, num_categories):
        image_input = Input(shape=(224, 224, 3))
        
        hidden_dim = 512 # todo: no idea why 512. figure out
        
        vgg_model = VGGFace(input_tensor=image_input, include_top=False)
        
        # only train the classifier
        #for layer in vgg_model.layers:
        #    layer.trainable = false
        
        last_layer = vgg_model.get_layer('pool5').output
        x = Flatten(name='flatten')(last_layer)
        x = Dense(hidden_dim, activation='relu', name='fc6')(x)
        x = Dense(hidden_dim, activation='relu', name='fc7')(x)
        out = Dense(num_categories, activation='softmax', name='fc8')(x)
        final_model = Model(image_input, out)
        
        # compile model using stochastic gradient descent
        sgd = SGD(lr=1e-3, momentum=0.9)
        final_model.compile(optimizer=sgd, loss='categorical_crossentropy', metrics=['accuracy'])

        return final_model
    
    def build_new_binary_model(self):
        vgg16 = VGG16(weights='imagenet')
                
        # add top classifier 
        fc2 = vgg16.get_layer('fc2').output
        prediction = Dense(1, activation='sigmoid', name='logit')(fc2)

        # put pretrained and classifier together to form new model for fine-tuning
        final_model = Model(inputs=vgg16.input, outputs=prediction)

        # compile model using stochastic gradient descent
        sgd = SGD(lr=1e-3, momentum=0.9)
        final_model.compile(optimizer=sgd, loss='binary_crossentropy', metrics=['accuracy'])

        return final_model

    def get_model(self, model_name):
        model_dir = self.final_model_dir + model_name
        model_path = "%s/model.json" % model_dir
        weights_path = "%s/weights.h5" % model_dir

        if not os.path.exists(model_dir):
            os.makedirs(model_dir)

        # first check if model already downloaded locally
        model_file = Path(model_path)
        weights_file = Path(weights_path)

        # get model from s3 if missing
        if not model_file.is_file() or not weights_file.is_file():
            (model_path, weigths_path) = self.get_s3_model(model_name, model_path, weights_path)

        # load json and create model
        json_file = open(model_path, 'r')
        loaded_model_json = json_file.read()
        json_file.close()
        loaded_model = model_from_json(loaded_model_json)
        loaded_model.load_weights(weights_path)

        return loaded_model

    def get_s3_model(self, model_name, final_model_path, final_weights_path):
        s3 = boto3.client('s3',
                            region_name='us-east-1',
                            aws_access_key_id=ACCESS_KEY,
                            aws_secret_access_key=SECRET_KEY)

        model_key = "%s/final_model/model.json" % model_name
        weights_key = "%s/final_model/weights.h5" % model_name

        # Download the file from S3
        s3.download_file(AMAZON_DS_BUCKET, model_key, final_model_path)
        s3.download_file(AMAZON_DS_BUCKET, weights_key, final_weights_path)

        return (final_model_path, final_weights_path)

    def save_s3_model(self, model_name,  model_path, weights_path, in_progress):
        today = str(datetime.date.today())
        # TODO: connect to s3 the same way as above + abstract out into utility
        s3 = boto3.resource('s3',
                           region_name='us-east-1',
                           aws_access_key_id=ACCESS_KEY,
                           aws_secret_access_key=SECRET_KEY)

        bucket = s3.Bucket(AMAZON_DS_BUCKET)
        model_status = "in_progress_model" if in_progress else "final_model"
        key_prefix = "%s/%s/" % (model_name, model_status)

        # add json model
        model_filename = today + "-" + "model.json"
        s3.Object(AMAZON_DS_BUCKET, key_prefix + model_filename).put(Body=open(model_path, 'rb'))

        # add weights file
        weights_filename = today + "-" + "weights.h5"
        s3.Object(AMAZON_DS_BUCKET, key_prefix + weights_filename).put(Body=open(weights_path, 'rb'))

        
         

