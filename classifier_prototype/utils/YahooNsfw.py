import subprocess
import logging
import subprocess
import os
import sys

file_path = os.path.abspath(os.path.dirname('__file__'))
path_args = file_path.split('/')
project_root_idx = path_args.index('giphyds') + 1
project_root_path = '/'.join(path_args[:project_root_idx])

if project_root_path not in sys.path:
    sys.path.append(project_root_path)

log_path = project_root_path + '/log/yahoo_nsfw_query_error.log'
logging.basicConfig(filename=log_path,level=logging.DEBUG)

"""
This class is a simple wrapper around yahoo's open source NSFW deep learning model
In order to call the model, you must have docker running and connected to Yahoo's image
Instructions on Yahoo's github:https://github.com/yahoo/open_nsfw
"""
class YahooNsfw():

    def get_probability(self,img_path):
        # call yahoo's nsfw model from command line. record errors in log
        path = os.path.abspath(os.path.join('vision'))
        img_path = "tmp/" + img_path.split("/")[-1]
        cmd = "/usr/bin/docker run --volume=%s:/workspace caffe:cpu python libs/open_nsfw/classify_nsfw.py --model_def libs/open_nsfw/nsfw_model/deploy.prototxt --pretrained_model libs/open_nsfw/nsfw_model/resnet_50_1by2_nsfw.caffemodel %s" % (path, img_path);
        cmdArray = cmd.split()
        try:
            result = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL)
            score = float(result.split()[-1])
            return score
        except OSError as e:
            logging.error("script failed on command %s with error %s \n" % (cmd, e))
