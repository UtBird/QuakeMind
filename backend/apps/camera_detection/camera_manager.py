from ultralytics import YOLO
import cv2
import threading
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

class VideoCaptureThread:
    def __init__(self, source=0):
        self.cap = cv2.VideoCapture(source)
        self.frame = None
        self.running = True
        self.lock = threading.Lock()

    def start(self):
        thread = threading.Thread(target=self.update, daemon=True)
        thread.start()

    def update(self):
        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                continue
            with self.lock:
                self.frame = frame

    def get_frame(self):
        with self.lock:
            return self.frame.copy() if self.frame is not None else None

    def stop(self):
        self.running = False
        self.cap.release()

def draw_results(frame, results, class_names, window_name):
    if results is None:
        cv2.imshow(window_name, frame)
        return
    for box in results.boxes.data.cpu().numpy():
        x1, y1, x2, y2, conf, cls = box
        x1, y1, x2, y2 = map(int, [x1, y1, x2, y2])
        label = f'{class_names[int(cls)]} {conf:.2f}'
        color = (255, 0, 102)
        cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
    cv2.imshow(window_name, frame)

def main():
    # Model yolları (models klasörüne taşındı)
    model1_path = BASE_DIR / "models" / "catlak.pt"
    model2_path = BASE_DIR / "models" / "bina.pt"

    # Modelleri yükle
    model1 = YOLO(str(model1_path))
    model2 = YOLO(str(model2_path))

    # Sınıf isimlerini al
    class_names1 = model1.names
    class_names2 = model2.names

    # Video yakalama başlat
    video_thread = VideoCaptureThread(0)
    video_thread.start()

    window1 = "catlak Tespiti"
    window2 = "Bina durumu"

    cv2.namedWindow(window1, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window1, 800, 600)
    cv2.namedWindow(window2, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(window2, 800, 600)

    try:
        while True:
            frame = video_thread.get_frame()
            if frame is None:
                continue

            # Tahmin sonuçlarını tutacak yapı
            results1 = [None]
            results2 = [None]

            # Model tahmin fonksiyonları
            def run_model1():
                results1[0] = model1.predict(source=frame, conf=0.6, verbose=False)[0]

            def run_model2():
                results2[0] = model2.predict(source=frame, conf=0.4, verbose=False)[0]

            # Thread'leri başlat
            t1 = threading.Thread(target=run_model1)
            t2 = threading.Thread(target=run_model2)
            t1.start()
            t2.start()
            t1.join()
            t2.join()

            # Sonuçları çiz
            draw_results(frame.copy(), results1[0], class_names1, window1)
            draw_results(frame.copy(), results2[0], class_names2, window2)

            # Çıkmak için 'q' tuşuna bas
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        video_thread.stop()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
