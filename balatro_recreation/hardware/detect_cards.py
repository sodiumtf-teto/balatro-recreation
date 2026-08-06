import cv2
from ultralytics import YOLO

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
        upper_half = img[:mid_y, :]
        lower_half = img[mid_y:, :]
        
        # 2. ArUco Detection (Upper Half)
        corners, ids, rejected = self.aruco_detector.detectMarkers(upper_half)
        arucos = []
        if ids is not None:
            aruco_data = []
            
            # Flatten the ids array so it's always a simple 1D list like [12, 24, 8]
            flat_ids = ids.flatten()
            
            for i in range(len(flat_ids)):
                aruco_id = int(flat_ids[i])
                # Find the leftmost X coordinate of this marker's 4 corners
                left_x = min(pt[0] for pt in corners[i][0])
                aruco_data.append((left_x, aruco_id))
            
            # Sort left-to-right based on the X coordinate
            aruco_data.sort(key=lambda x: x[0])
            arucos = [item[1] for item in aruco_data]
            
        # 3. Card Detection (Lower Half)
        # YOLO predict accepts the cropped numpy array directly
        result = self.model.predict(lower_half, verbose=False)[0]
        cards = [] 
        cards_names = set() 
        summary = result.summary()

        for card in summary:
            if card['confidence'] >= self.conf:
                card_name = card['name']
                if card_name not in cards_names:
                    cards_names.add(card_name)
                    # The X-coordinates are unaffected by the horizontal slice
                    card_left = min(card['box']['x1'], card['box']['x2'])
                    cards.append((card_left, card_name))
                    
        cards.sort(key=lambda x: x[0])
        sorted_cards = [card[1] for card in cards]
        
        return arucos, sorted_cards

def format_cards(cards):
    return [str(card).upper() for card in cards]

# --- Usage Example ---
# detector = BoardDetector("best.pt")
# aruco_ids, cards = detector.detect("table_image.jpg")
# formatted_cards = format_cards(cards)
# print(f"ArUcos: {aruco_ids} | Cards: {formatted_cards}")