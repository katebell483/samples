import os
import numpy as np
import datetime
import boto3
import sys
from keras.preprocessing.image import ImageDataGenerator
from keras.callbacks import ModelCheckpoint, EarlyStopping

"""
AWS INFO REMOVED
"""

file_path = os.path.abspath(os.path.dirname('__file__'))
path_args = file_path.split('/')
project_root_idx = path_args.index('imgds') + 1
project_root_path = '/'.join(path_args[:project_root_idx])

if project_root_path not in sys.path:
    sys.path.append(project_root_path)

from vision.VisionModels import VisionModels
from vision.VisionPreprocess import VisionPreprocess
from vision.utils.VisionUtils import VisionUtils

class VisionTrain():

    def __init__(self):
        # make tmp dir for data if not already there
        self.tmp_dir = project_root_path + '/vision/tmp/'
        if not os.path.exists(self.tmp_dir):
            os.makedirs(self.tmp_dir)
        
    def _get_s3_conn(self):
        s3 = boto3.resource('s3',
               region_name='us-east-1',
               aws_access_key_id=ACCESS_KEY,
               aws_secret_access_key=SECRET_KEY)
        return s3

    def _get_data(self, model_name, i):  

        # get ds bucket from S3
        s3 = self._get_s3_conn()
        bucket = s3.Bucket(AMAZON_DS_BUCKET)
        
        # limit i to num files avail for processing
        prefix = "%s/numpy_train_data_" % model_name    
        npz_files = [i.key for i in bucket.objects.filter(Prefix=prefix) if i.key[-4:] == ".npz"]   
        i = i % len(npz_files)

        
        # download, uncompress + save chosen training + test files
        train_file = 'numpy_train_data_%s.npz' % i
        test_file = 'numpy_test_data_%s.npz' % i
        tmp_train_file = '%s/%s' % (self.tmp_dir, train_file)
        tmp_test_file = '%s/%s' % (self.tmp_dir, test_file)
        bucket.download_file('%s/%s' % (model_name, train_file), tmp_train_file)
        bucket.download_file('%s/%s' % (model_name, test_file), tmp_test_file)
        train_data = np.load(tmp_train_file)
        test_data = np.load(tmp_test_file)
        
        # remove the numpy files
        os.remove(tmp_train_file)
        os.remove(tmp_test_file)
        
        return train_data, test_data

    def _img_generator(self, model_name, i):
        
        # get data will randomly pull one of the model's npz data files from s3
        train_data, test_data = self._get_data(model_name, i)
        
        # shuffle data
        train_data_count = len(train_data["images"])
        train_idx = np.random.choice(np.arange(train_data_count), 
                               train_data_count, 
                               replace=False)
        
        train_images = train_data["images"][train_idx]
        train_labels = train_data["labels"][train_idx]
        
        test_data_count = len(test_data["images"])
        test_idx = np.random.choice(np.arange(test_data_count), 
                                    test_data_count, 
                                    replace=False)
                               
        test_images = test_data["images"][test_idx]
        test_labels = test_data["labels"][test_idx]
        
        # yields a tuple of numpy arrays for train + test sets of images + labels
        yield (train_images, 
               train_labels, 
               test_images, 
               test_labels)

    def _build_data_generators(self, model_name):
        # do data augmentation on the fly with this keras util
        preprocess = VisionPreprocess()
        train_datagen = ImageDataGenerator(preprocessing_function=preprocess.preprocess_input_vgg,
                                           rotation_range=40,
                                           width_shift_range=0.2,
                                           height_shift_range=0.2,
                                           shear_range=0.2,
                                           zoom_range=0.2,
                                           horizontal_flip=True,
                                           fill_mode='nearest')
      
        # validation data augmentation is v. minimal-- just formats images for the vgg model
        validation_datagen = ImageDataGenerator(preprocessing_function=preprocess.preprocess_input_vgg)
      
        # get initial test set to fit the image processing datagens on
        (X_train, Y_train, X_test, Y_test) = next(self._img_generator(model_name, 0))
        
        # compute quantities required for featurewise normalization
        train_datagen.fit(X_train)
        validation_datagen.fit(X_test)

        return train_datagen, validation_datagen

    # TODO: support other models not just VGG
    def train(self, model_name, model_arch, data_size, num_epochs, num_categories, classifier_type):

        # get pretrained vgg model specific to type of classifier
        models = VisionModels()
        if classifier_type == "facial_recognition":
            model = models.build_new_facial_recognition_model(num_categories)
        elif classifier_type == "binary":
            model = models.build_new_binary_model()
        else:   
            print("Training exited: Unsupported Classifier Type %s. Must be 'binary' or 'facial_recognition'" % classifier_type)
            return False # unsupported classifier TODO: standard multilabel image classifier 
      
        # build data generators
        train_datagen, validation_datagen = self._build_data_generators(model_name)
        
        # how many batches of test data should we process? data is stored in max 10k batches
        num_cycles = int(round(data_size / 10000)) + 1
        
        # create dir for saved model
        in_progress_model_dir = '%s/vision/models/in_progress/%s/%s' % (project_root_path, model_name, model_arch)
        if not os.path.exists(in_progress_model_dir):
            os.makedirs(in_progress_model_dir)
        
        # save the best model
        updated_model_weights_path = '%s/%s_updated_weights_%s.h5' % (in_progress_model_dir, model_arch, str(num_epochs))
        checkpointer = ModelCheckpoint(filepath = updated_model_weights_path, verbose = 0, save_best_only = True)
        
        # stop if no substantial improvement for 10 epochs
        early_stopping_callback = EarlyStopping(monitor='val_loss', min_delta=0.005, patience=10)

        # use today's date filenames
        today = str(datetime.date.today())
      
        # train the model across the dataset
        # note, if the dataset is smallish (like 10k) it will only do one cycle.
        # this loop is for larger datasets that won't fit into memeory all at once
        for x in range(0, num_cycles):
        
            # get batch of train & test data
            (X_train, Y_train, X_test, Y_test) = next(self._img_generator(model_name, x))
            
            # encode string labels to binary for multiclass models
            if classifier_type == "binary":
                Y_train_encoded = Y_train
                Y_test_encoded = Y_test
            else:
                utils = VisionUtils()
                Y_train_encoded = utils.encode_labels(Y_train, num_categories)
                Y_test_encoded = utils.encode_labels(Y_test, num_categories)
            
        
            # create data generators from train/validation dirs
            datagen_batch_size = 32
            train_generator = train_datagen.flow(X_train, Y_train_encoded, batch_size=datagen_batch_size)
            validation_generator = validation_datagen.flow(X_test, Y_test_encoded, batch_size=datagen_batch_size)
      
            # fine-tune the model
            train_data = model.fit_generator(train_generator,
                                steps_per_epoch=len(X_train)/datagen_batch_size,
                                epochs=num_epochs,
                                validation_data=validation_generator,
                                validation_steps=len(X_test)/datagen_batch_size,
                                callbacks=[checkpointer, early_stopping_callback])
                        
            # save model + weights to s3
            updated_model_path = '%s/%s_updated_model_%s.json' % (in_progress_model_dir, model_arch, today)
            model_json = model.to_json()
            with open(updated_model_path, "w") as json_file:
                json_file.write(model_json)
            in_progress = True
            models.save_s3_model(model_name, updated_model_path, updated_model_weights_path, in_progress)

if __name__ == "__main__":

    # parse command line arguments
    model_name = str(sys.argv[1])
    model_arch = str(sys.argv[2])
    num_categories = int(sys.argv[3])
    data_size = int(sys.argv[4])
    num_epochs = int(sys.argv[5])
    classifier_type = str(sys.argv[6])

    train = VisionTrain()
    train.train(model_name, model_arch, data_size, num_epochs, num_categories, classifier_type)


