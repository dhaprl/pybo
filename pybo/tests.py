import os
import cv2
from ultralytics import YOLO
from pathlib import Path
#
# YOLOv8 얼굴 감지 모델 불러오기
base_dir = os.path.join(Path(__file__).resolve().parent, 'ai_files')
path = os.path.join(base_dir, 'ai_models', 'YOLOv8', 'yolov8n-face.pt'),
model = YOLO(path)
#
def detect_face(img_path):
    #
    # 이미지 불러오기
    img = cv2.imread(img_path)
    #
    # 이미지 감지 수행
    results = model.predict(img_path, conf=0.1, imgsz=1280, max_det=1000)
    #
    # 감지된 결과를 이미지에 그리기
    for result in results:
        boxes = result.boxes
        for box in boxes:
            # 바운딩 박스 좌표 및 신뢰도 추출
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            conf = box.conf.item()
            cls = box.cls.item()
            # label = f"human"
            label = f"{conf:.2f}"
            #
            # 바운딩 박스 그리기SSS
            cv2.rectangle(img, (x1, y1), (x2, y2), (10, 250, 50), 1)  # 파란색 사각형 그리기
            cv2.putText(img, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (10, 250, 50), 2)
            #
        #
    #
    cv2.imwrite(img_path, img)
    output_path = os.path.join(base_dir, 'output', os.path.basename(img_path))
    #
    return output_path
    #
#
def start_ai():
    img_folder = os.path.join(base_dir, 'image_test'),
    img_files = [f for f in os.listdir(img_folder) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    #
    for img_file in img_files:
        # path.join() 함수를 사용하여 디렉토리 경로와 파일 이름을 연결합니다.
        img_path = os.path.join(img_folder, img_file)
        #
        output_path = detect_face(img_path)
        #
        return output_path
        #
    #
#