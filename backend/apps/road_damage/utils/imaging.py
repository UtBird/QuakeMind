"""Image encoding/overlay helpers for the road-damage analysis result.

Kept separate from fastapi_app.py so apps/road_damage/worker.py (a
ProcessPoolExecutor worker entrypoint) can import these without importing
fastapi_app.py itself.
"""
import base64
import io

import cv2
import numpy as np
from PIL import Image


def image_array_to_b64(image_arr):
    """Encode an RGB numpy array (or single-channel mask) as a base64 PNG data URI."""
    arr = image_arr
    if arr.dtype != np.uint8:
        arr = arr.astype(np.uint8)
    img = Image.fromarray(arr)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return "data:image/png;base64," + base64.b64encode(buffer.getvalue()).decode()


def build_damage_overlay(original_img, road_mask, pred_mask, intersection):
    """Reproduce the Streamlit RDA color overlay: cyan=open road, yellow=debris, red=debris-on-road."""
    vis_img = original_img.copy()

    yellow_overlay = np.zeros_like(vis_img)
    yellow_overlay[:] = [255, 255, 0]
    red_overlay = np.zeros_like(vis_img)
    red_overlay[:] = [255, 0, 0]
    cyan_overlay = np.zeros_like(vis_img)
    cyan_overlay[:] = [0, 255, 255]

    cyan_idx = (road_mask == 1) & (intersection == 0)
    blended_cyan = cv2.addWeighted(vis_img, 0.3, cyan_overlay, 0.7, 0)
    vis_img[cyan_idx] = blended_cyan[cyan_idx]

    mask_idx = (pred_mask == 1) & (intersection == 0)
    blended_yellow = cv2.addWeighted(vis_img, 0.5, yellow_overlay, 0.5, 0)
    vis_img[mask_idx] = blended_yellow[mask_idx]

    kernel = np.ones((9, 9), np.uint8)
    thick_intersection = cv2.dilate(intersection, kernel, iterations=2)
    intersection_idx = thick_intersection == 1
    blended_red = cv2.addWeighted(vis_img, 0.1, red_overlay, 0.9, 0)
    vis_img[intersection_idx] = blended_red[intersection_idx]

    return vis_img


def build_segmentation_overlay(original_img, pred_mask):
    seg_overlay = original_img.copy()
    damage_color = np.zeros_like(seg_overlay)
    damage_color[:] = [255, 50, 50]
    damage_idx = pred_mask == 1
    blended = cv2.addWeighted(seg_overlay, 0.4, damage_color, 0.6, 0)
    seg_overlay[damage_idx] = blended[damage_idx]
    return seg_overlay
