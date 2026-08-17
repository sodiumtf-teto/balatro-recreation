import cv2
from ultralytics import YOLO
from game import state

class BoardDetector:
    def __init__(self, weights_path, conf=0.5):
        print(f"Loading YOLO model from {weights_path}...")
        self.model = YOLO(weights_path, task='detect')
        self.conf = conf
        
        # Initialize ArUco detector (DICT_4X4_250)
        # Note: This uses the modern OpenCV 4.7+ ArucoDetector API
        self.aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_250)
        self.aruco_params = cv2.aruco.DetectorParameters()
        self.aruco_detector = cv2.aruco.ArucoDetector(self.aruco_dict, self.aruco_params)

    def detect(self, image_path):
        # 1. Load and split the image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Could not load image at {image_path}")
            
        height, width = img.shape[:2]
        mid_y = height // 2
        
        # Region of Interest (ROI) splitting
        joker_area = img[:mid_y, :int((width/4)*3)]
        play_area = img[mid_y:, :]
        consumables_area = img[:mid_y, int((width/4)*3):width]

        # Jokers
        corners, ids, rejected = self.aruco_detector.detectMarkers(joker_area)
        joker_arucos = []
        if ids is not None:
            aruco_data = []
            flat_ids = ids.flatten()
            for i in range(len(flat_ids)):
                aruco_id = int(flat_ids[i])
                left_x = min(pt[0] for pt in corners[i][0])
                aruco_data.append((left_x, aruco_id))
            aruco_data.sort(key=lambda x: x[0])
            joker_arucos = [item[1] for item in aruco_data]
        # Play Area
        result = self.model.predict(play_area, verbose=False)[0]
        cards = [] 
        cards_names = set() 
        summary = result.summary()
        for card in summary:
            if card['confidence'] >= self.conf:
                card_name = card['name']
                if card_name not in cards_names:
                    cards_names.add(card_name)
                    card_left = min(card['box']['x1'], card['box']['x2'])
                    cards.append((card_left, card_name))
        cards.sort(key=lambda x: x[0])
        sorted_cards = [card[1] for card in cards]
        # Consumables
        corners, ids, rejected = self.aruco_detector.detectMarkers(consumables_area)
        consumables_arucos = []
        if ids is not None:
            aruco_data = []
            flat_ids = ids.flatten()
            for i in range(len(flat_ids)):
                aruco_id = int(flat_ids[i])
                left_x = min(pt[0] for pt in corners[i][0])
                aruco_data.append((left_x, aruco_id))
            aruco_data.sort(key=lambda x: x[0])
            consumables_arucos = [item[1] for item in aruco_data]
            
        return joker_arucos, consumables_arucos, sorted_cards

def format_cards(cards):
    return [str(card).upper() for card in cards]

# --- Usage Example ---
# detector = BoardDetector("best.pt")
# aruco_ids, cards = detector.detect("table_image.jpg")
# formatted_cards = format_cards(cards)
# print(f"ArUcos: {aruco_ids} | Cards: {formatted_cards}")