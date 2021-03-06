import cv2
import numpy as np
import glob
import time
import RC_Controls as rc

def filter_region(image, vertices):
    """
    Create the mask using the vertices and apply it to the input image
    """
    mask = np.zeros_like(image)
    if len(mask.shape) == 2:
        cv2.fillPoly(mask, vertices, 255)
    else:
        cv2.fillPoly(mask, vertices, (255,) * mask.shape[2])  # in case, the input image has a channel dimension
    return cv2.bitwise_and(image, mask)


def select_region(image):
    """
    It keeps the region surrounded by the `vertices` (i.e. polygon).  Other area is set to 0 (black).
    """
    # first, define the polygon by vertices
    rows, cols = image.shape[:2]
    bottom_left = [cols * 0.1, rows * 0.95]
    top_left = [cols * 0.4, rows * 0.6]
    bottom_right = [cols * 0.9, rows * 0.95]
    top_right = [cols * 0.6, rows * 0.6]
    # the vertices are an array of polygons (i.e array of arrays) and the data type must be integer
    vertices = np.array([[bottom_left, top_left, top_right, bottom_right]], dtype=np.int32)
    return filter_region(image, vertices)


def draw_lines(image, lines, color=(0, 0, 255), thickness=2, make_copy=True):
    # the lines returned by cv2.HoughLinesP has the shape (-1, 1, 4)
    if make_copy:
        image = np.copy(image) # don't want to modify the original
    for line in lines:
        for x1,y1,x2,y2 in line:
            cv2.line(image, (x1, y1), (x2, y2), color, thickness)
    return image


def slope(x1, y1, x2, y2):
    return (float(y2)-float(y1))/(float(x2)-float(x1))


def lane_slopes_finder(img, lane):
    h, w, c = img.shape
    slopes = []
    intercepts = []
    for line in lane:
        for x1, y1, x2, y2 in line:
            m = slope(x1, y1, x2, y2)
            intercept = y1 - m * x1
            slopes.append(m)
            intercepts.append(intercept)

    mean_slope = np.mean(slopes)
    x_top = int((mean_slope*(h/2))+(w/2))
    x_bottom = int((-mean_slope*(h/2))+(w/2))
    cv2.line(img, (w/2, 0), (w/2, h), (255, 0, 0), 2)
    cv2.line(img, (x_bottom, h), (x_top, 0), (0, 255, 0), 2)
    return mean_slope

def limit(num,minn,maxx):
    if num<minn:
        num=minn
    elif num>maxx:
        num=maxx
    return num


        
# ---------------------------------------------------------------

cap = cv2.VideoCapture('videos/solidWhiteRight.mp4')
times = []

while cap.isOpened():
    time1 = time.time()
    ret, road = cap.read()
    road = cv2.resize(road, (420,240))
    gray_road = cv2.cvtColor(road, cv2.COLOR_BGR2GRAY)
    roi = select_region(gray_road)
    retval, threshold = cv2.threshold(roi, 200, 255, cv2.THRESH_BINARY)
    edges = cv2.Canny(threshold, 100, 150)
    houghLines = cv2.HoughLinesP(edges, rho=1, theta=np.pi/180, threshold=20, minLineLength=20, maxLineGap=300)
    lane_lines = draw_lines(road, houghLines)
    mean_slope = lane_slopes_finder(lane_lines, np.array(houghLines))
    # cv2.imshow('Road', road)
    # cv2.imshow('GrayScale Road', gray_road)
    # cv2.imshow('THRESHOLD', threshold)
    # cv2.imshow('Edges', edges)
    # cv2.imshow('ROI', roi)
    angle= limit(float(rc.translate(mean_slope,3,-3,0,180)),0,180)
    rc.update(angle)
    cv2.imshow('Lanes', lane_lines)
    
    time2 = time.time()
    times.append(time2-time1)
    print ('\n')
    print ('Angle:',angle)
    print ('Slope:',mean_slope)
    print ('FPS:',np.mean(times)**-1)
    k = cv2.waitKey(30) & 0xFF
    if k == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
