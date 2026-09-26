import math
import os
import cv2
from PIL import Image

# Template Dimensions
CANVAS_WIDTH = 184
CANVAS_HEIGHT = 384

# Coordinates & Dimensions
ART_POS = (3, 3)
ART_SIZE = (178, 238)

ARUCO_POS = (28, 248)
ARUCO_MODULE_SIZE = 16  # Each ArUco grid unit = 16x16 px

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SPRITES_DIR = os.path.join(BASE_DIR, "sprites")
HARDWARE_DIR = os.path.join(BASE_DIR, "hardware")
DARK_TEMPLATE_PATH = os.path.join(SPRITES_DIR, "base_card_dark.png")
LIGHT_TEMPLATE_PATH = os.path.join(SPRITES_DIR, "base_card_light.png")

OUTPUT_PATH = os.path.join(HARDWARE_DIR, "epaper_image.png")

# Sub-directories for card components
ART_DIR = os.path.join(SPRITES_DIR, "playing_cards")
ENHANCEMENTS_DIR = os.path.join(SPRITES_DIR, "enhancements")
SEAL_DIR = os.path.join(SPRITES_DIR, "seals")


def generate_aruco_tag(aruco_id: int, module_size: int = ARUCO_MODULE_SIZE) -> Image.Image:
    """
    Generates a 4x4_1000 ArUco tag scaled to 16x16 px per module,
    with a 1-module white border around it (128x128 px total).
    """
    marker_px = 6 * module_size
    
    aruco_dict = cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_1000)
    marker_np = cv2.aruco.generateImageMarker(aruco_dict, aruco_id, marker_px)
    marker_img = Image.fromarray(marker_np).convert("RGBA")

    # Add 1 module (16px) white border around the marker -> 128x128 px
    total_size = 8 * module_size
    tag_canvas = Image.new("RGBA", (total_size, total_size), (255, 255, 255, 255))
    tag_canvas.paste(marker_img, (module_size, module_size))

    return tag_canvas


def draw_playing_card(card, aruco_id: int = None) -> Image.Image:
    """
    Composites card art, enhancements, and an ArUco code onto the appropriate suit template.
    """
    # Determine Theme (Dark for Hearts/Diamonds, Light for Spades/Clubs)
    theme = "dark" if card.suit in ["Hearts", "Diamonds"] else "light"
    template_path = DARK_TEMPLATE_PATH if theme == "dark" else LIGHT_TEMPLATE_PATH

    # 1. Load the base frame template (184x384)
    if os.path.exists(template_path):
        canvas = Image.open(template_path).convert("RGBA")
    else:
        bg_color = (0, 0, 0, 255) if theme == "dark" else (255, 255, 255, 255)
        canvas = Image.new("RGBA", (CANVAS_WIDTH, CANVAS_HEIGHT), bg_color)

    # Check for enhancements
    enhancement = getattr(card, 'enhancement', None)
    if enhancement:
        enhancement = enhancement.lower()

    # 2. Draw Enhancement Layer (Below card art, skipped if Stone)
    if enhancement and enhancement != "stone":
        enh_filename = f"{enhancement}_{theme}.png"
        enh_path = os.path.join(ENHANCEMENTS_DIR, enh_filename)
        if os.path.exists(enh_path):
            enh_img = Image.open(enh_path).convert("RGBA")
            if enh_img.size != ART_SIZE:
                enh_img = enh_img.resize(ART_SIZE, Image.NEAREST)
            canvas.paste(enh_img, ART_POS, enh_img)
        else:
            print(f"Warning: Enhancement texture not found at {enh_path}")

    # 3. Draw Main Card Art (or Stone Override)
    if enhancement == "stone":
        stone_filename = f"stone_{theme}.png"
        stone_path = os.path.join(ENHANCEMENTS_DIR, stone_filename)
        if os.path.exists(stone_path):
            stone_img = Image.open(stone_path).convert("RGBA")
            if stone_img.size != ART_SIZE:
                stone_img = stone_img.resize(ART_SIZE, Image.NEAREST)
            canvas.paste(stone_img, ART_POS, stone_img)
        else:
            print(f"Warning: Stone texture not found at {stone_path}")
    else:
        # Load & Paste Normal Card Art (178x238 at 3, 3)
        standard_filename = f"{card.rank}_{card.suit}.png"
        typo_filename = f"{card.rank}__{card.suit}.png"  # Handles "A__Hearts.png" typo from exports
        
        art_path = os.path.join(ART_DIR, standard_filename)
        if not os.path.exists(art_path):
            art_path = os.path.join(ART_DIR, typo_filename)

        if os.path.exists(art_path):
            art_img = Image.open(art_path).convert("RGBA")
            if art_img.size != ART_SIZE:
                art_img = art_img.resize(ART_SIZE, Image.NEAREST)
            canvas.paste(art_img, ART_POS, art_img)
        else:
            print(f"Warning: Art not found at {art_path}")

    # Check for seal
    seal = getattr(card, 'seal', None)
    if seal:
        seal = seal.lower()

    # 4. Draw Seal
    if seal:
        seal_filename = f"{seal}_{theme}.png"
        seal_path = os.path.join(SEAL_DIR, seal_filename)
        if os.path.exists(seal_path):
            seal_img = Image.open(seal_path).convert("RGBA")
            if seal_img.size != ART_SIZE:
                seal_img = seal_img.resize(ART_SIZE, Image.NEAREST)
            canvas.paste(seal_img, ART_POS, seal_img)
        else:
            print(f"Warning: Seal texture not found at {seal_path}")

    # 5. Draw Edition


    # 6. Generate & Paste ArUco Tag (at 28, 248)
    if aruco_id is not None:
        aruco_img = generate_aruco_tag(aruco_id)
        canvas.paste(aruco_img, ARUCO_POS, aruco_img)

    # 7. Convert to 1-bit monochrome for the e-paper display
    return canvas.convert("1")


def draw_card(card_object, aruco_id: int = None):
    """
    Main entry point for generating and saving e-paper card images.
    """
    if hasattr(card_object, 'rank') and hasattr(card_object, 'suit'):
        img = draw_playing_card(card_object, aruco_id)
    else:
        raise NotImplementedError("Jokers and Consumables drawing not implemented yet!")

    if OUTPUT_PATH:
        img.save(OUTPUT_PATH)
    return img


def format_balatro_number(value):
    try:
        f_val = float(value)
        if math.isinf(f_val) or math.isnan(f_val) or f_val > 1.79e308:
            return "naneinf"

        # 1 digit: up to 2 decimal places
        if f_val < 10:
            return f"{f_val:.2f}".rstrip("0").rstrip(".")

        # 2 digits: up to 1 decimal place
        elif f_val < 100:
            return f"{f_val:.1f}".rstrip("0").rstrip(".")

        # 3+ digits: no decimals, rounded
        elif f_val < 1_000_000:
            return str(round(f_val))
    except (ValueError, TypeError, OverflowError):
        pass

    # From here on, handle large integers and check against the 1.79e308 limit
    try:
        val_int = int(value)
        if float(val_int) > 1.79e308:
            return "naneinf"
    except (ValueError, TypeError, OverflowError):
        return "naneinf"

    s = str(val_int)
    exponent = len(s) - 1

    exp_str = f"E{exponent}"
    allowed_mantissa_len = 7 - len(exp_str)

    if allowed_mantissa_len < 3:
        head = int(s[:2])
        rounded = (head + 5) // 10

        if rounded == 10:
            return f"1E{exponent + 1}"

        return f"{rounded}{exp_str}"

    sig_figs = allowed_mantissa_len - 1
    head = int(s[:sig_figs + 1])
    rounded = (head + 5) // 10

    if len(str(rounded)) > sig_figs:
        exponent += 1
        exp_str = f"E{exponent}"
        allowed_mantissa_len = 7 - len(exp_str)

        if allowed_mantissa_len < 3:
            return f"1{exp_str}"

        decimals = "0" * (allowed_mantissa_len - 2)
        return f"1.{decimals}{exp_str}"

    r_str = str(rounded)
    return f"{r_str[0]}.{r_str[1:]}{exp_str}"