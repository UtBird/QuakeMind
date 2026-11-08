from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
MODEL_PATHS = {
    "crack_detection": BASE_DIR / "models" / "catlak.pt",
    "building_detection": BASE_DIR / "models" / "bina.pt",
}


def launch_camera_detection():
    from camera_manager import main as camera_main

    camera_main()


def get_camera_model_paths():
    return MODEL_PATHS.copy()
