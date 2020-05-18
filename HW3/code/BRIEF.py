import numpy as np
import cv2
import os
from scipy.spatial.distance import cdist
from keypointDetect import DoGdetector
import math
import matplotlib.pyplot as plt


def makeTestPattern(patch_width=9, nbits=256):
    '''
    Creates Test Pattern for BRIEF

    Run this routine for the given parameters patch_width = 9 and n = 256

    INPUTS
    patch_width - the width of the image patch (usually 9)
    nbits      - the number of tests n in the BRIEF descriptor

    OUTPUTS
    compareX and compareY - LINEAR indices into the patch_width x patch_width image 
                            patch and are each (nbits,) vectors. 
    '''
    #############################
    compareX = np.random.randint(0, 80, nbits)
    compareY = np.random.randint(0, 80, nbits)
    
    return  compareX, compareY

# load test pattern for Brief
#test_pattern_file = '../results/testPattern.npy'
#if os.path.isfile(test_pattern_file):
    # load from file if exists
    #compareX, compareY = np.load(test_pattern_file)
#else:
    # produce and save patterns if not exist
   # compareX, compareY = makeTestPattern()
    #if not os.path.isdir('../results'):
        #os.mkdir('../results')
    #np.save(test_pattern_file, [compareX, compareY])
    
    


def computeBrief(im, locsDoG, compareX, compareY):
    '''
    Compute Brief feature
     INPUT
     locsDoG - locsDoG are the keypoint locations returned by the DoG
               detector.
     levels  - Gaussian scale levels that were given in Section1.
     compareX and compareY - linear indices into the 
                             (patch_width x patch_width) image patch and are
                             each (nbits,) vectors.
    
    
     OUTPUT
     locs - an m x 3 vector, where the first two columns are the image
    		 coordinates of keypoints and the third column is the pyramid
            level of the keypoints.
     desc - an m x n bits matrix of stacked BRIEF descriptors. m is the number
            of valid descriptors in the image and will vary.
    '''
    if len(im.shape)==3:
        im = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
    if im.dtype!='float' or np.amax(im)>1:
        im = im.astype('float')/255
    locs = np.empty((0, 3))
    desc = np.empty((0, len(compareX)))
    patch_size = 9
    add_patch = math.floor(patch_size/2)
    
    for y,x,level in locsDoG:
        #eliminate patches which may extend out of the image
        
        if (x-add_patch<0) or (x+add_patch>=im.shape[0]) or (y-add_patch<0) or (y+add_patch>=im.shape[1]):
            continue
        #create locs for which patches exist
        X = np.asarray([y, x, level]).reshape(1,3)
        
        locs = np.append(locs, X, axis=0)
        
        
        patch = np.empty((patch_size, patch_size))
        for i in range(patch_size):
            
            patch[i,:] = im[int(x-add_patch+i), int(y-add_patch):int(y+add_patch+1)]
            #print(patch[i,:])
        patch = patch.reshape(patch_size**2, 1)
        d = []
        for i in range(len(compareX)):
            
            if patch[compareX[i]]<patch[compareY[i]]:
                
                d.append(1)
            else:
                d.append(0)
        d = np.asarray(d)
        
        d = d.reshape(-1, len(compareX))
        desc = np.append(desc, d, axis=0)
        
    return locs, desc



def briefLite(im):
    '''
    INPUTS
    im - gray image with values between 0 and 1

    OUTPUTS
    locs - an m x 3 vector, where the first two columns are the image coordinates 
            of keypoints and the third column is the pyramid level of the keypoints
    desc - an m x n bits matrix of stacked BRIEF descriptors. 
            m is the number of valid descriptors in the image and will vary
            n is the number of bits for the BRIEF descriptor
    '''
    
    
    test_pattern_file = '../results/testPattern.npy'
    compareX, compareY = np.load(test_pattern_file)
    locsDoG, gaussian_pyramid = DoGdetector(im)
    locs, desc = computeBrief(im, locsDoG, compareX, compareY)

    return locs, desc

def briefMatch(desc1, desc2, ratio=0.8):
    '''
    performs the descriptor matching
    inputs  : desc1 , desc2 - m1 x n and m2 x n matrix. m1 and m2 are the number of keypoints in image 1 and 2.
                                n is the number of bits in the brief
    outputs : matches - p x 2 matrix. where the first column are indices
                                        into desc1 and the second column are indices into desc2
    '''
    D = cdist(np.float32(desc1), np.float32(desc2), metric='hamming')
    # find smallest distance
    ix2 = np.argmin(D, axis=1)
    d1 = D.min(1)
    # find second smallest distance
    d12 = np.partition(D, 2, axis=1)[:,0:2]
    d2 = d12.max(1)
    r = d1/(d2+1e-10)
    is_discr = r<ratio
    ix2 = ix2[is_discr]
    ix1 = np.arange(D.shape[0])[is_discr]

    matches = np.stack((ix1,ix2), axis=-1)
    return matches

def plotMatches(im1, im2, matches, locs1, locs2):
    fig = plt.figure()
    # draw two images side by side
    imH = max(im1.shape[0], im2.shape[0])
    im = np.zeros((imH, im1.shape[1]+im2.shape[1]), dtype='uint8')
    im[0:im1.shape[0], 0:im1.shape[1]] = cv2.cvtColor(im1, cv2.COLOR_BGR2GRAY)
    im[0:im2.shape[0], im1.shape[1]:] = cv2.cvtColor(im2, cv2.COLOR_BGR2GRAY)
    plt.imshow(im, cmap='gray')
    for i in range(matches.shape[0]):
        pt1 = locs1[matches[i,0], 0:2]
        pt2 = locs2[matches[i,1], 0:2].copy()
        pt2[0] += im1.shape[1]
        x = np.asarray([pt1[0], pt2[0]])
        y = np.asarray([pt1[1], pt2[1]])
        plt.plot(x,y,'r')
        plt.plot(x,y,'g.')
    plt.show()
    
    

if __name__ == '__main__':
    # test makeTestPattern
    compareX, compareY = makeTestPattern()
    test_pattern_file = '../results/testPattern.npy'
    np.save(test_pattern_file, [compareX, compareY])
    
    # test briefLite
    #im = cv2.imread('../data/model_chickenbroth.jpg')
    #locs, desc = briefLite(im)
    #fig = plt.figure()
    # plt.imshow(cv2.cvtColor(im, cv2.COLOR_BGR2GRAY), cmap='gray')
    # plt.plot(locs[:,0], locs[:,1], 'r.')
    # plt.draw()
    # plt.waitforbuttonpress(0)
    # plt.close(fig)
    # test matches
    im1 = cv2.imread('../data/incline_L.png')
    im2 = cv2.imread('../data/incline_R.png') 
    locs1, desc1 = briefLite(im1)
   
    locs2, desc2 = briefLite(im2)
    
    #locs2, desc2 = briefLite(im2)
    matches = briefMatch(desc1, desc2)
    plotMatches(im1,im2,matches,locs1,locs2)