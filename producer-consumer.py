#!/usr/bin/python3
from threading import Thread, Condition
import cv2
import os
import time
import random


# Global variables
outputDir = 'frames'
clipFileName = 'dog.mp4'
queue1 = []
queue2 = []
condition1 = Condition()
condition2 = Condition()
MAX_NUM = 10

# Threads
class ExtractThread(Thread):
    def run(self):
        global queue1
        # open the video clip
        vidcap = cv2.VideoCapture(clipFileName)

        # initialize frame count
        count = 0

        # create the output directory if it doesn't exist
        if not os.path.exists(outputDir):
          print("Output directory {} didn't exist, creating".format(outputDir))
          os.makedirs(outputDir)

        # read one frame
        success,image = vidcap.read()

        print("Reading frame {} {} ".format(count, success))

        while success:
            condition1.acquire()
            if len(queue1) == MAX_NUM:
                print("Queue 1 full, extracting frames is paused")
                condition1.wait()
            # write the current frame out as a jpeg image
            cv2.imwrite("{}/frame_{:04d}.jpg".format(outputDir, count), image)
            success,image = vidcap.read()
            print('Reading frame {}'.format(count))
            queue1.append(count)
            count += 1
            condition1.notify()
            condition1.release()
            #time.sleep(random.random())
        queue1.append(-1)
        print("ExtractThread ends")



class ConvertThread(Thread):
    def run(self):
        global queue1
        global queue2
        while True:
            condition1.acquire()
            if not queue1:
                print('Nothing in queue 1')
                condition1.wait()
            count = queue1.pop(0)

            if count == -1:
                break
            # get the next frame file name
            inFileName = "{}/frame_{:04d}.jpg".format(outputDir, count)

            # load the next file
            inputFrame = cv2.imread(inFileName, cv2.IMREAD_COLOR)

            print("Converting frame {}".format(count))

            # convert the image to grayscale
            grayscaleFrame = cv2.cvtColor(inputFrame, cv2.COLOR_BGR2GRAY)

            # generate output file name
            outFileName = "{}/grayscale_{:04d}.jpg".format(outputDir, count)

            # write output file
            cv2.imwrite(outFileName, grayscaleFrame)

            # generate input file name for the next frame
            inFileName = "{}/frame_{:04d}.jpg".format(outputDir, count)

            # load the next frame
            inputFrame = cv2.imread(inFileName, cv2.IMREAD_COLOR)

            condition1.notify()
            condition1.release()

            condition2.acquire()

            if len(queue2) == MAX_NUM:
                print("Queue 2 full, extracting frames is paused")
                condition2.wait()
            queue2.append(count)
            condition2.notify()
            condition2.release()
            #time.sleep(random.random())
        queue2.append(-1)
        print("ConvertThread ends")

class DisplayThread(Thread):
    def run(self):
        global queue2
        frameDelay = 42
        startTime = time.time()

        while True:
            condition2.acquire()
            if not queue2:
                print('Nothing in queue 2')
                condition2.wait()
            count = queue2.pop(0)

            if count == -1:
                break

            # Generate the filename for the first frame
            frameFileName = "{}/grayscale_{:04d}.jpg".format(outputDir, count)

            # load the frame
            frame = cv2.imread(frameFileName)

            print("Displaying frame {}".format(count))
            # Display the frame in a window called "Video"
            cv2.imshow("Video", frame)

            # compute the amount of time that has elapsed
            # while the frame was processed
            elapsedTime = int((time.time() - startTime) * 1000)
            print("Time to process frame {} ms".format(elapsedTime))

            # determine the amount of time to wait, also
            # make sure we don't go into negative time
            timeToWait = max(1, frameDelay - elapsedTime)

            # Wait for 42 ms and check if the user wants to quit
            if cv2.waitKey(timeToWait) and 0xFF == ord("q"):
                break

            # get the start time for processing the next frame
            startTime = time.time()

            condition2.notify()
            condition2.release()
            #time.sleep(random.random())
        cv2.destroyAllWindows()

ExtractThread().start()
ConvertThread().start()
DisplayThread().start()
