from ultralytics import YOLO

class CardDetector:
    def __init__(self, weights_path, conf=0.5):
        print(f"Loading YOLO model from {weights_path}...")
        self.model = YOLO(weights_path, task='detect')
        self.conf = conf
    def detect(self, image_path):
        result = self.model.predict(image_path, verbose=False)[0]
        cards = [] # a list of tuples (left, card_name)
        cards_names = set() # a set for faster deduplication
        summary = result.summary()

        for card in summary:
            if card['confidence'] >= self.conf:
                card_name = card['name']
                if card_name not in cards_names:
                    cards_names.add(card_name)
                    card_left = min(card['box']['x1'], card['box']['x2'])
                    cards.append((card_left, card_name))
        cards.sort(key=lambda x: x[0])
        return [card[1] for card in cards]

def format_cards(cards):
    formatted = []
    for card in cards:
        # Force the label to uppercase (turns '9d' into '9D')
        formatted.append(str(card).upper())
    return formatted