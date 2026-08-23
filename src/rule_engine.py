from arduino.app_utils import App, Bridge
from arduino.app_bricks.web_ui import WebUI
from arduino.app_bricks.video_objectdetection import VideoObjectDetection


# ============================================================
# INITIALIZATION
# ============================================================

ui = WebUI()
bridge = Bridge()

detector = VideoObjectDetection(
    confidence=0.30,
    debounce_sec=0.0
)


# ============================================================
# SYSTEM STATE
# ============================================================

flame_detected = False
burner_on = False
cloth_detected = False


# ============================================================
# CLASS DEFINITIONS
# ============================================================

# Kitchen model:
# Class 1 = Flame

FLAME_CLASSES = {
    "1",
    "class_1",
    "flame",
    "fire"
}


# Cloth model:
# Either of its two classes represents cloth.
#
# If your cloth model uses class 0 and class 1,
# both are included here.

CLOTH_CLASSES = {
    "0",
    "class_0",
    "1",
    "class_1",
    "cloth",
    "towel"
}


# Burner model

BURNER_ON_CLASSES = {
    "burner_on",
    "burner_active",
    "burneron"
}


BURNER_OFF_CLASSES = {
    "burner_off",
    "burneroff"
}


# ============================================================
# LED CONTROL
# ============================================================

def set_alert(active):

    if active:

        bridge.call(
            "set_alert",
            1
        )

    else:

        bridge.call(
            "set_alert",
            0
        )


# ============================================================
# RULE ENGINE
# ============================================================

def evaluate_rules(
    flame,
    burner,
    cloth
):

    # --------------------------------------------------------
    # RULE 1:
    # FLAME + CLOTH
    # --------------------------------------------------------

    if flame and cloth:

        return {
            "hazard": "FIRE HAZARD",
            "message": "Flame and cloth detected",
            "alert": True
        }


    # --------------------------------------------------------
    # RULE 2:
    # FLAME ONLY
    # --------------------------------------------------------

    if flame:

        return {
            "hazard": "FLAME DETECTED",
            "message": "Flame detected",
            "alert": False
        }


    # --------------------------------------------------------
    # RULE 3:
    # BURNER ON
    # --------------------------------------------------------

    if burner:

        return {
            "hazard": "BURNER ACTIVE",
            "message": "Burner is ON",
            "alert": False
        }


    # --------------------------------------------------------
    # RULE 4:
    # CLOTH ONLY
    # --------------------------------------------------------

    if cloth:

        return {
            "hazard": "CLOTH DETECTED",
            "message": "Cloth detected",
            "alert": False
        }


    # --------------------------------------------------------
    # RULE 5:
    # SAFE
    # --------------------------------------------------------

    return {
        "hazard": "SAFE",
        "message": "Kitchen condition normal",
        "alert": False
    }


# ============================================================
# PROCESS AI DETECTIONS
# ============================================================

def process_detections(detections):

    flame = False
    burner = False
    cloth = False

    output_detections = []


    # ========================================================
    # READ DETECTIONS
    # ========================================================

    for class_name, values in detections.items():

        if isinstance(values, dict):

            values = [values]


        name = (
            str(class_name)
            .strip()
            .lower()
            .replace("-", "_")
            .replace(" ", "_")
        )


        for value in values:

            confidence = float(
                value.get(
                    "confidence",
                    0.0
                )
            )


            # Ignore weak detections

            if confidence < 0.30:
                continue


            box = value.get(
                "bounding_box_xyxy"
            )

            if box is None:

                box = value.get(
                    "bounding_box"
                )


            # ------------------------------------------------
            # SAVE DETECTION
            # ------------------------------------------------

            output_detections.append({

                "class_name":
                    str(class_name),

                "confidence":
                    round(
                        confidence,
                        3
                    ),

                "bounding_box":
                    box
            })


            # =================================================
            # FLAME
            # =================================================

            if name in FLAME_CLASSES:

                flame = True


            # =================================================
            # CLOTH
            # =================================================

            elif name in CLOTH_CLASSES:

                cloth = True


            # =================================================
            # BURNER ON
            # =================================================

            elif name in BURNER_ON_CLASSES:

                burner = True


            # =================================================
            # BURNER OFF
            # =================================================

            elif name in BURNER_OFF_CLASSES:

                burner = False


    # ========================================================
    # APPLY RULE ENGINE
    # ========================================================

    result = evaluate_rules(
        flame,
        burner,
        cloth
    )


    # ========================================================
    # CONTROL LED
    # ========================================================

    set_alert(
        result["alert"]
    )


    # ========================================================
    # WEB UI
    # ========================================================

    ui.send_message(

        "detection",

        message={

            "detections":
                output_detections,

            "hazard":
                result["hazard"],

            "message":
                result["message"],

            "flame":
                flame,

            "burner_on":
                burner,

            "cloth":
                cloth,

            "alert":
                result["alert"]
        }
    )


# ============================================================
# REGISTER CALLBACK
# ============================================================

detector.on_detect_all(
    process_detections
)


# ============================================================
# START APPLICATION
# ============================================================

App.run()
