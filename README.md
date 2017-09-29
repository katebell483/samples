# samples

These four samples represent the great range of work that I've done as an engineer and student. They vary in terms of intended audience, complexity, language, and utility. 

### Sample 1: CS_131_HW_2: "Naive parsing of context free grammars" (ocaml)
I completed this homework assignment for Paul Eggert's programming class at UCLA in the fall of 2016. It's written in OCaml, a language I was unfamiliar with before his class. This simple program for me represented the difference between academic software and the kind I had been writing for the last three years as a software developer. It was a deceptively challenging assignment. The program was simple-- create a program that parsed text based on certain grammar rules-- but the highly recursive strategy necessary to complete this task was not. More on this assignment [here](http://web.cs.ucla.edu/classes/fall16/cs131/hw/hw2.html).

### Sample 2: Classifier_Prototype: A quick-and-dirty image classification model (python)
I fine-tuned a pre-trained model out of oxford to be able to recognize 20 celebrities that weren't represented in the original training dataset. I used TensorFlow and Keras to write the program and wrapped the resulting model in a simple flask app so that it could be queried from a http interface. The latter part of the code isn't represented in the sample for the sake of brevity. Since the prototype was made to be used on animations, rather than still images, you will see that the preprocessing steps take frames into account. More technical details can be found in the folder's [README file](https://github.com/katebell483/samples/blob/master/classifier_prototype/README.md).

### Sample 3: quick_d3_nytimes_experiment: A simple data visualization project using d3 (javascript)
I wanted to take d3 for a spin and was specifically interested in creating models with a 3D effect, so I started with a revolving globe example as my jumping off point (original animation found [here](https://bl.ocks.org/animateddata/0949801eba0d51c80f22490db665f8c3)). In choosing the data I wanted to model, my criteria were simple: realtime, real world data that was easily queryable and politically relevant. The New York Times API provided just this. I sought to answer the question "what countries are covered by the most popular news of the day?" To do this I used the NYTimes Popular Api, which returns data about the most consumed articles in a section, over a given period of time. I chose the world section and 24 hours. I then took the geolocation metadata provided for each article and passed it to Google's geolocation API to get the location data in terms of latitude and longitude. This data was then projected onto the globe as simple pins. The result is straightforward, but maintains a certain poetic quality. 

### Sample 4: simple_share_counter_etl: Scala code for tracking shared content (scala)
This etl (extract, transform, load) program uses the data sink and source as it's driving framework. I choose this sample because it represents one of the first times I wrote Scala and its minimal style left a lasting impression.  It pulls a SQS message, extracts the data from it, transforms the data so that it can be properly stored in a redshift database, and loads said data into redshift. It worked on batches of these messages at a time and ran as a nightly job, which was regulated using Luigi. 
