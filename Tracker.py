from collections import deque
import cv2
import imutils
import numpy as np
from matplotlib import pyplot as plt


class ContourTracker(object):

    def __init__(self):
        self.position = deque(maxlen=16)
        self.center = None

    def track_contours(self, cam_frame):
        radius = None

        lt = np.array([75, 35, 85])
        ut = np.array([90, 215, 255])

        blurred = cv2.GaussianBlur(cam_frame, (11, 11), 0)
        hsv = cv2.cvtColor(blurred, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lt, ut)
        mask = cv2.erode(mask, None, iterations=2)
        mask = cv2.dilate(mask, None, iterations=2)

        cntrs = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        cntrs = imutils.grab_contours(cntrs)
        if len(cntrs) > 0:
            c = max(cntrs, key=cv2.contourArea)
            ((x, y), radius) = cv2.minEnclosingCircle(c)
            moments = cv2.moments(c)
            self.center = (int(moments["m10"] / moments["m00"]), int(moments["m01"] / moments["m00"]))
            self.position.append(self.center)

            if radius > 10:
                cv2.circle(cam_frame, (int(x), int(y)), int(radius), (0, 255, 255), 2)
                cv2.circle(cam_frame, self.center, 5, (0, 0, 255), -1)

        [cv2.line(cam_frame, self.position[i - 1], self.position[i], (0, 255, 0),
                  int(np.sqrt(32 / float(i + 1)) * 2.5)) for i in range(1, len(self.position))]

        return cam_frame, radius

    def get_center(self):
        return self.center


class ROITracker(object):

    def __init__(self):
        self.position_arr = []
        self.position_dq = deque(maxlen=16)
        self.roi_tracker = cv2.TrackerCSRT_create()
        self.init_bb = None

    def track_roi(self, cam_frame):
        pos = None
        (success, box) = self.roi_tracker.update(cam_frame)

        if success:
            (x, y, w, h) = [int(v) for v in box]
            cv2.rectangle(cam_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            x_center = int(x + (w / 2))
            y_center = int(y + (h / 2))
            cv2.circle(cam_frame, (x_center, y_center), 1, (0, 255, 0), thickness=2)
            cv2.circle(cam_frame, (x_center, y_center), 0, (0, 255, 0), thickness=2)
            pos = (x_center, y_center)
            self.position_arr.append(pos)
            self.position_dq.append(pos)

            [cv2.line(cam_frame, self.position_dq[i - 1], self.position_dq[i], (0, 255, 0),
                      int(np.sqrt(32 / float(i + 1)) * 2.5)) for i in range(1, len(self.position_dq))]

        return pos

    def set_init_bb(self, init_bb):
        self.init_bb = init_bb

    def init_roi_tracker(self, cam_frame):
        self.roi_tracker.init(cam_frame, self.init_bb)

    def get_position_arr(self):
        return self.position_arr

    def plot_trace(self, predictions):
        plt_act = None
        plt_pred = None
        for (pos, pred) in zip(self.get_position_arr(), predictions):
            y_neg = np.negative(pos[1])
            y_neg_pred = np.negative(pred[1])
            plt_act = plt.scatter(pos[0], y_neg, marker=6, c="indianred", label="Actual Position")
            plt_pred = plt.scatter(pred[0], y_neg_pred, marker="x", c="mediumseagreen", label="Predicted Position")

        plt.legend(handles=[plt_act, plt_pred])
        plt.show()
