import cv2
import math
import numpy as np

class Helper:

    @classmethod
    def display_time_difference_in_ms(cls, endTime, startTime):
        return str(int((endTime-startTime) * 1000)) + " ms"
    
    
    @classmethod
    def convert_string_to_bool(cls, env):
        if env in ['True', 'TRUE', '1', 'y', 'YES', 'Y', 'Yes']:
            return True
        elif env in ['False', 'FALSE', '0', 'n', 'NO', 'N', 'No']:
            return False
        else:
            raise ValueError('Could not convert string to bool.')
        

    @classmethod
    def unwarp_perspective(cls, img, src, dst):
        src = np.array(src, dtype=np.float32)
        dst = np.array(dst, dtype=np.float32)

        h, w = img.shape[:2]
        # use cv2.getPerspectiveTransform() to get M, the transform matrix, and Minv, the inverse
        M = cv2.getPerspectiveTransform(src, dst)
        # use cv2.warpPerspective() to warp your image to a top-down view
        warped = cv2.warpPerspective(img, M, (w, h), flags=cv2.INTER_LINEAR)

        # Crop the image to the bounds of the rectification region
        # Get the min and max x, y coordinates from the destination points
        min_x = int(min(dst[:, 0]))
        max_x = int(max(dst[:, 0]))
        min_y = int(min(dst[:, 1]))
        max_y = int(max(dst[:, 1]))

        # Crop the warped image using the bounding box
        cropped_warped = warped[min_y:max_y, min_x:max_x]
        
        return warped

