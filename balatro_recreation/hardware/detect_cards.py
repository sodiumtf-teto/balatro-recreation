import cv2
from game import state

class BoardDetector:
    def __init__(self):
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_1000)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)
        parameters = cv2.aruco.DetectorParameters()
        # Make it more lenient with lighting changes and thresholding:
        parameters.adaptiveThreshWinSizeMin = 3
        parameters.adaptiveThreshWinSizeMax = 23
        parameters.adaptiveThreshWinSizeStep = 10
        parameters.minMarkerPerimeterRate = 0.02  # Allows detecting smaller/further markers if needed
        parameters.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX  # Better edge precision

    def _extract_sorted_arucos(self, image_roi):
        """Helper to detect and sort ArUco IDs from left to right."""
        corners, ids, rejected = self.aruco_detector.detectMarkers(image_roi)
        if ids is None:
            return []
            
        aruco_data = []
        flat_ids = ids.flatten()
        for i in range(len(flat_ids)):
            aruco_id = int(flat_ids[i])
            # Min x-coordinate of the 4 corners of the marker
            left_x = min(pt[0] for pt in corners[i][0])
            aruco_data.append((left_x, aruco_id))
            
        aruco_data.sort(key=lambda x: x[0])
        return [item[1] for item in aruco_data]

    def detect(self, image_path):
        # 1. Load and slice the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image at {image_path}")
            
        height, width = img.shape[:2]
        first_third_y = height // 3
        second_third_y = height // 3 * 2
        
        # Region of Interest (ROI) boundaries
        joker_area = img[:first_third_y, :int((width/4)*3)]
        consumables_area = img[:first_third_y, int((width/4)*3):width]
        play_area = img[first_third_y:second_third_y, :]
        held_area = img[second_third_y:, :]

        # 2. Extract raw IDs per region
        joker_area_ids = self._extract_sorted_arucos(joker_area)
        consumables_area_ids = self._extract_sorted_arucos(consumables_area)
        play_area_raw_ids = self._extract_sorted_arucos(play_area)
        held_area_ids = self._extract_sorted_arucos(held_area)

        # 3. Segregate the Play Area IDs
        play_area_cards = []
        play_area_jokers = []
        play_area_consumables = []

        for aruco_id in play_area_raw_ids:
            if 500 <= aruco_id <= 551:
                play_area_cards.append(aruco_id)
            elif aruco_id < 199: # Assuming your jokers map up to ~146
                play_area_jokers.append(aruco_id)
            else:
                # Anything else (e.g., 200-499) gets lumped as a consumable
                play_area_consumables.append(aruco_id)
            
        return (
            joker_area_ids, 
            consumables_area_ids, 
            play_area_cards, 
            play_area_jokers, 
            play_area_consumables,
            held_area_ids
        )