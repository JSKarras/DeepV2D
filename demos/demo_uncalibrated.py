import sys
sys.path.append('deepv2d')

import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt

import argparse
import cv2
import os
import time
import glob
import random

from core import config
from deepv2d import DeepV2D



def load_video(video_file, n_frames=8, start_idx=0):
    cap = cv2.VideoCapture(args.video)

    # Check if camera opened successfully
    if (cap.isOpened()== False): 
        print("Error opening video stream or file")

    count = 1
    rate = 3

    images = []
    while cap.isOpened():

        ret, img = cap.read()

        if ret and (count-1) >= start_idx:
            if count % rate == 0:
                #cv2.imshow("image", img)
                cv2.waitKey(100)

                img = cv2.resize(img, None, fx=0.4, fy=0.4, interpolation=cv2.INTER_AREA)
                ht, wd, _ = img.shape
                ht1 = (ht // 64) * 64 
                wd1 = (wd // 64) * 64

                crop_y = (ht - ht1) // 2
                crop_x = (wd - wd1) // 2

                img = img[crop_y:crop_y+ht1, crop_x:crop_x+wd1]
                images.append(img)
        elif (count-1) < start_idx:
            pass
        else:
            break

        count += 1

        if len(images) >= n_frames:
            break

    keyframe_index = len(images) // 2
    inds = np.arange(len(images))
    
    inds = inds[~np.equal(inds, keyframe_index)]
    inds = [keyframe_index] + inds.tolist()
    #print(inds)
    images = np.stack([images[i] for i in inds], axis=0)
    return images


def main(args):
    cfg = config.cfg_from_file(args.cfg)
  
    all_images = load_video(args.video, n_frames=args.n_frames)

    print("Batching a total of ", len(all_images), " frames...")
    with tf.Session() as sess:
        images = all_images[:7]
        deepv2d = DeepV2D(cfg, args.model, mode=args.mode, image_dims=[None, images.shape[1], images.shape[2]],
        use_fcrn=True, is_calibrated=False, use_regressor=False)
        deepv2d.set_session(sess)
        for i in range(args.n_frames//7):
          start_idx = 7*i
          print("Frames Batch #", i+1, ": frames ", start_idx, " - ", start_idx+7)
          images = all_images[start_idx:start_idx+7]
          depths, poses = deepv2d(images, viz=True, iters=args.n_iters, start_idx=start_idx, cmap=args.cmap)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cfg', default='cfgs/uncalibrated.yaml', help='config file used to train the model')
    parser.add_argument('--model', default='models/uncalibrated.ckpt', help='path to model checkpoint')
    parser.add_argument('--scale', action='store_true', help='path to model checkpoint')
    parser.add_argument('--video', help='path to your video')

    parser.add_argument('--mode', default='keyframe', help='keyframe or global pose optimization')
    parser.add_argument('--fcrn', action="store_true", help='use fcrn for initialization')
    parser.add_argument('--n_iters', type=int, default=16, help='number of iterations to use')
    parser.add_argument('--n_frames', type=int, default=7, help='number of video frames to use')
    parser.add_argument('--cmap', default="binary", help='color map to use for depth visualization')
    args = parser.parse_args()

    main(args)
