# Model Specifications:
Pre-trained VGG16 CNN. Trained on dataset comprised of 2,622 celebrity identities, achieving ~92% accuracy against the YouTube Faces Database + ~97% accuracy against Labeled Faces in the Wild***. The images for used for training were pulled from Bing + Google images searches. The resulting model, VGG Face, is open source and published by Oxford. Further details on the methodology + results are detailed in the following paper: https://www.robots.ox.ac.uk/~vgg/publications/2015/Parkhi15/parkhi15.pdf. A new softmax layer was appended to the above pre-trained model for our classification purposes. The set of 20 labels used in this test case as follows:
  
  1. Rihanna
  2. Selena Gomez
  3. Ariana Grande
  4. Beyonce
  5. Taylor Swift
  6. Kim Kardashian
  7. Cristiano Ronaldo
  8.  Justin Bieber
  9.  Kylie Jenner
  10. The Rock
  11. Drake
  12. Emma Watson
  13. Melissa McCarthy
  14. Meryl Streep
  15. Ryan Gosling
  16. Hillary Clinton
  17. Donald Trump
  18. Prince
  19. Kendall Jenner
  20. Serena Williams
  
*** Labeled Faces in the Wild is a benchmarking dataset used widely in experiments addressing the issue of unconstrained face recognition (ie facial recognition in context). It is a dataset of public figures pulled largely from the web. Overall this represents a cleaner set than the Youtube data which is pulled from video content. Due to the animated nature of our content, it follows that the frames extracted in our training set would fall closer in kind to YouTube's DB.  

#### Data Collection: 
I followed the same tactic taken by the researchers at Oxford by pulling images from both Bing + Google, as well as from our own DB. While over 176k GIFS were considered for training, only a fraction of that original set was ultimately used (~30%).

So to refine data collected, the Oxford group had a manual verification step. Human annotators culled through the images and discarded any not seen as reaching a certain quality level. Due to limited time and resources, I was not able to do this manual step. As such, the google + bing results were left unfiltered. However, since our data has been decorated by the google vision api, I was able to use google's labels to validate our own tags. I discarded images whose tags were not verified by google. 

To further clean the data, images with more than one face were tossed due to the inherent ambiguity of identification. Images without faces were likewise removed.

The oxford group also had a more sophisticated step for removing duplicates or near duplicates. I simply removed duplicate media_urls from our dataset. Improving this step might offer in increased training accuracy. 

The dataset starts with a total of 204843 images and is then whittled down to about a quarter of the size as images are removed from the set during the above filtering process (~55k images in total). The dataset is then broken into test + training sets and then again into equal sized batches of roughly 2k images, which were then stored as compressed numpy files in S3.

There are many opportunities for improvement in this process, including both programatic and manual strategies. The way that we extract validate + extract faces from our own data could benefit from a step that determined which frame of the GIF offered the best quality face, for example. We could also develop quick editorial tools that would allow an individual to visually browse a dataset and click to remove undesirable content. Furthermore, in this case I considered every GIF in our databse labeled one of the above 20 names. I think this query could be more targeted. A more refined and smaller dataset might be preferable to a larger and more unwieldy one. The oxford group, for example, ended with 1000 images for each person. We have considerably more than that (even after filtering) and the returns on these increased numbers are unclear.

#### Preprocessing:
Each image is passed into our preprocessing API, which is a wrapper around CMU's Openface library which uses dlib to do feature extraction + alignment. The face in each image is detected, the image is then warped such that the facial features are aligned to a standard template and finally cropped to a 224 x 224 square about said face (standard dimensions for the VGG model). 

Each image is further preprocessed on the fly via Keras' standard VGG preprocessing function which subtracts the mean RGB pixel intensity from each image.

Training images also undergo data augmentation in this step to reduce the risk of overfitting and increase accuracy. I believe there is also opportunity for improvement in this area via testing different augmentation techniques and levels.

#### Training:
A single batch of ~2k images is pulled from s3 and  fed through the model in increments of 32 images at a time. These sets are preprocessed + augmented on the fly as described above. Each epoch steps through the data in these batches until all images have been used. The entire model is trained (rather than in classic fine-tuning where only the classification layer is trained) using a very low learning rate (.001). Returning to the classic fine-tuning strategy is worth investigating since our data should be very similar to the original data used for training. 

Each dataset is trained over 40 epochs. While further improvement above this number seemed improbable, this parameter is easily tested and tuned. Databricks has a notebook describing how to do distributed hyperparameter tuning, which you can read about here. Tuning of this sort would likely result in higher accuracy. 

The most accurate set of weights produced within each set of epochs is saved.

In the end, the final model was trained over 21 of these batches images (again with 40 epochs for each batch). However, I was still seeing incremental improvement within the last batch. It would be worth passing the data through the trained model again or retraining on the same data for say 42 cycles instead of 21 to find exactly where the improvement stops.

#### Results:
The final validation accuracy of the model during training was just over 93%.  Accuracy across labels differs slightly. Do to the opaque strategy used in data collection, I can only speculate this has to do with two factors: how similar the face was to members of the original (Oxford) dataset and the quality + number of images used in our training-- Beyonce has much wider pool to pull from than say Christian Ronaldo. To address this issue, different thresholds could be applied across different labels. The ROC curves below can be used to this end. Another peculiarity of the model is that it tends to overgeneralize in some respects.  Michelle Obama ~ Beyonce, Melania Trump ~ Meryl Streep, young white woman ~ Taylor Swift. It is my assumption that this has to do with the small numbers of labels we used in training-- the face space we created was so well articulated that new content tends to fit much more squarely in one category than another leading to an overconfidence of identification. Creating label-specific thresholds might address this issue. Including more people in the training data might also. All of my work can be extended to a much larger dataset. 

To test trained models I created a Jupyter notebook that evaluates each model over four tactics: measuring simple accuracy, drawing ROC curves for each label as well as an average ROC curve across the data, building a confusion matrix + evaluating the model across live API results. 

Sample metric results from the notebook:

Confusion Matrix: A confusion matrix visualizes the question "How many times does image with label x get classified x, as opposed to labels j or k?"

![](result_imgs/confusion_matrix_celeb_may_2017.png?raw=true)

Receiver Operating Characteristic (ROC) Curves: ROC curves aid in the selection of a proper threshold for classification by comparing true and false positive rates across thresholds.

![](result_imgs/roc_curve_1.png?raw=true)

![](result_imgs/roc_curve_2.png?raw=true)





