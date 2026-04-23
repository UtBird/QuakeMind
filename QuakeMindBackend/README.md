# QuakeMind

QuakeMind is a multi-module disaster support project that brings together:

- Turkish disaster text analysis
- satellite-based road damage assessment
- earthquake risk analysis
- live camera-based crack and building detection

The repository is organized as a single project with multiple apps under `apps/`, plus one unified Streamlit entry point at the root.

## Overview

QuakeMind combines different disaster-response workflows in one place:

- `Disaster NLP`
  Classifies Turkish disaster-related text, extracts locations, and visualizes results on a map.
- `Road Damage`
  Uses satellite imagery and segmentation to estimate road damage and access conditions.
- `Earthquake Risk`
  Computes city-level earthquake risk using historical events, fault proximity, and derived risk features.
- `Camera Detection`
  Runs live camera-based crack and building-status detection using YOLO models.

## Repository Structure

```text
QuakeMind/
├── main.py
├── README.md
├── .gitignore
└── apps/
    ├── camera_detection/
    │   ├── app.py
    │   ├── camera_manager.py
    │   └── models/
    ├── disaster_nlp/
    │   ├── app.py
    │   ├── requirements.txt
    │   ├── models/
    │   └── src/
    ├── earthquake_risk/
    │   ├── data/
    │   ├── data_manager.py
    │   ├── gui_app.py
    │   ├── main.py
    │   ├── map_visualizer.py
    │   ├── models/
    │   ├── requirements.txt
    │   └── risk_engine.py
    └── road_damage/
        ├── app.py
        ├── models/
        ├── requirements.txt
        └── utils/
```

## Unified App

Run the unified interface from the repository root:

```bash
streamlit run main.py
```

Available pages in the unified interface:

- `Disaster Text Analysis`
- `Satellite Road Damage Analysis`
- `Earthquake Risk Panel`
- `Camera Detection`

## Individual Apps

### Disaster NLP

Location:

```text
apps/disaster_nlp
```

Run directly:

```bash
cd apps/disaster_nlp
streamlit run app.py
```

Main capabilities:

- Turkish disaster text preprocessing
- text classification
- NER-based location extraction
- map visualization with Folium

### Road Damage

Location:

```text
apps/road_damage
```

Run directly:

```bash
cd apps/road_damage
streamlit run app.py
```

Main capabilities:

- area selection from map layers
- road damage segmentation
- road network accessibility analysis
- open vs blocked route estimation

### Earthquake Risk

Location:

```text
apps/earthquake_risk
```

Recommended usage is through the unified interface. A desktop-style local UI also exists:

```bash
cd apps/earthquake_risk
python3 main.py
```

Main capabilities:

- historical earthquake data update
- city-based risk estimation
- nearby event analysis
- filtered fault-line rendering around selected coordinates

### Camera Detection

Location:

```text
apps/camera_detection
```

Relevant files:

- `apps/camera_detection/app.py`
- `apps/camera_detection/camera_manager.py`

Main capabilities:

- live webcam processing
- crack detection
- building-status detection
- parallel YOLO inference

## Requirements

Recommended Python version:

```text
Python 3.12
```

Example virtual environment setup:

```bash
python3 -m venv venv
source venv/bin/activate
```

Install dependencies app by app:

```bash
pip install -r apps/disaster_nlp/requirements.txt
pip install -r apps/road_damage/requirements.txt
pip install -r apps/earthquake_risk/requirements.txt
```

Notes:

- On Linux, the `earthquake_risk` desktop UI may require `python3-tk`.
- Camera detection requires webcam access.

## Model Sources

Some large model files are intentionally hosted outside GitHub and are downloaded automatically when missing.

### Automatically Downloaded Models

#### Disaster NLP classification model

Hugging Face repository:

```text
https://huggingface.co/Utbird/EqTwitterTr
```

Expected local directory:

```text
apps/disaster_nlp/models/2kveri/
├── config.json
├── model.safetensors
├── tokenizer.json
└── tokenizer_config.json
```

Current code behavior:

- if the local classification model directory is incomplete or missing, the app downloads the required files from `Utbird/EqTwitterTr`

Relevant code:

- [apps/disaster_nlp/src/classification.py](/home/utku/Desktop/QuakeMind/apps/disaster_nlp/src/classification.py:1)

#### Road Damage segmentation model

Hugging Face repository:

```text
https://huggingface.co/Utbird/dispath_optimized_mitb4_focal_dice30
```

Expected local file:

```text
apps/road_damage/models/optimized_mitb4_focal_dice30.pth
```

Current code behavior:

- if `optimized_mitb4_focal_dice30.pth` is missing, the app downloads it automatically from `Utbird/dispath_optimized_mitb4_focal_dice30`

Relevant code:

- [apps/road_damage/utils/inference.py](/home/utku/Desktop/QuakeMind/apps/road_damage/utils/inference.py:1)

### Other Models Kept in the Repository

These are currently small enough to remain in the repo:

- `apps/camera_detection/models/catlak.pt`
- `apps/camera_detection/models/bina.pt`
- `apps/earthquake_risk/models/*.pt`

### External NER Model

The NER model is currently loaded from Hugging Face:

```text
yhaslan/turkish-earthquake-tweets-ner
```

Repository:

```text
https://huggingface.co/yhaslan/turkish-earthquake-tweets-ner
```

## How Model Download Works

### Disaster NLP

When the local classification model is not available, the code downloads:

- `config.json`
- `model.safetensors`
- `tokenizer.json`
- `tokenizer_config.json`

from:

```text
Utbird/EqTwitterTr
```

### Road Damage

When the default segmentation weight file is not available, the code downloads:

- `optimized_mitb4_focal_dice30.pth`

from:

```text
Utbird/dispath_optimized_mitb4_focal_dice30
```

## Usage Flow

### Unified Interface

1. Activate your Python environment.
2. Install the required dependencies.
3. Run `streamlit run main.py`.
4. Select the desired module from the sidebar.
5. If a required large model is missing, the app will download it automatically.

### Disaster NLP

1. Select a sample text or enter custom text.
2. Run the analysis.
3. Review category, confidence score, and extracted location.
4. Inspect the map output.

### Road Damage

1. Select a city or area.
2. Choose or draw the region on the map.
3. Confirm the model path.
4. Run the analysis.
5. Inspect the segmentation and road accessibility results.

### Earthquake Risk

1. Select a city or enter manual coordinates.
2. Optionally refresh the earthquake dataset.
3. Run the risk analysis.
4. Review the result summary, map, heat layer, and technical details.

### Camera Detection

1. Open the camera page.
2. Start camera detection.
3. Observe the OpenCV windows.
4. Press `q` to close the camera windows.

## Technical Notes

- `streamlit_folium` is used for interactive maps.
- `catboost`, `geopy`, and `pandas` are required for earthquake risk analysis.
- `ultralytics` and `opencv-python` are required for camera detection.
- `segmentation-models-pytorch` is required for the road-damage model.
- large model weights are intentionally hosted on Hugging Face instead of GitHub.

## License and Distribution Note

Please verify the redistribution rights, training data constraints, and model licenses before publishing model weights broadly. This is especially important for any external or third-party models referenced by the project.
