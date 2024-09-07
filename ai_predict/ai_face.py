import logging
import os
import cv2
import dlib
import torch
import torch.nn as nn
import numpy as np
import pickle
import random
import face_recognition
from PIL import Image, ImageDraw, ImageFont
from torchvision import models, transforms
from tqdm import tqdm
from ultralytics import YOLO
from mtcnn import MTCNN
import time
import piexif
from abc import ABC, abstractmethod
import io
import shutil
from pathlib import Path
import warnings

# =========================
# 불필요한 경고 메시지 숨기기
# =========================
warnings.filterwarnings("ignore", category=UserWarning)

# =========================
# 로깅 설정: INFO 레벨 이상의 메시지만 출력
# =========================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# =========================
# 추상화: 얼굴 탐지기 인터페이스
# =========================
class FaceDetector(ABC):
    @abstractmethod
    def detect_faces(self, image):
        pass
        #
    #
#
# =========================
# Dlib 얼굴 탐지기 구현
# =========================
class DlibFaceDetector(FaceDetector):
    def __init__(self, model_path):
        #
        logging.info(f"Dlib 모델 loading 중...\n{model_path}")
        self.detector = dlib.cnn_face_detection_model_v1(model_path)
        logging.info(f"Dlib 모델 load 완료")
        #
    #
    def detect_faces(self, image):
        #
        logging.info("Dlib을 사용하여 얼굴 탐지 중...")
        faces = [(d.rect.left(), d.rect.top(), d.rect.right(), d.rect.bottom()) for d in self.detector(image, 1)]
        logging.info(f"Dlib 얼굴 탐지 완료, {len(faces)}개의 얼굴 검출.")
        #
        return faces
        #
    #
#
# =========================
# YOLO 얼굴 탐지기 구현
# =========================
class YOLOFaceDetector(FaceDetector):
    def __init__(self, model_path):
        #
        logging.info(f"YOLO 모델 loading 중...\n{model_path}")
        self.detector = YOLO(model_path)
        logging.info(f"YOLO 모델 load 완료")
        #
    #
    def detect_faces(self, image_path):
        #
        logging.info("YOLO를 사용하여 얼굴 탐지 중...")
        results = self.detector.predict(image_path, conf=0.35, imgsz=1280, max_det=1000)
        faces = [(int(box.xyxy[0][0]), int(box.xyxy[0][1]), int(box.xyxy[0][2]), int(box.xyxy[0][3])) for result in results for box in result.boxes]
        logging.info(f"YOLO 얼굴 탐지 완료, {len(faces)}개의 얼굴 검출.")
        #
        return faces
        #
    #
#
# =========================
# MTCNN 얼굴 탐지기 구현
# =========================
class MTCNNFaceDetector(FaceDetector):
    def __init__(self):
        #
        logging.info(f"MTCNN 모델 loading 중...")
        self.detector = MTCNN()
        logging.info("MTCNN 모델 load 완료")
        #
    #
    def detect_faces(self, image):
        #
        logging.info("MTCNN을 사용하여 얼굴 탐지 중...")
        faces = [(f['box'][0], f['box'][1], f['box'][0] + f['box'][2], f['box'][1] + f['box'][3]) for f in self.detector.detect_faces(image)]
        logging.info(f"MTCNN 얼굴 탐지 완료, {len(faces)}개의 얼굴 검출.")
        #
        return faces
        #
    #
#
# =========================
# 얼굴 탐지 관리자 클래스 - SRP를 따르고, 다형성 활용
# =========================
class FaceDetectionManager:
    def __init__(self, detectors):
        self._detectors = detectors
        #
    #
    # 얼굴 탐지 함수
    def detect_faces(self, image, image_path=None):
        #
        logging.info("얼굴 탐지 프로세스 시작")
        all_faces = []
        #
        for detector in self._detectors:
            #
            # YOLO 탐지기는 이미지 경로를 필요로 함
            if isinstance(detector, YOLOFaceDetector) and image_path:
                faces = detector.detect_faces(image_path)
            else:
                faces = detector.detect_faces(image)
                #
            #
            all_faces.extend(faces)
            #
        #
        logging.info(f"얼굴 탐지 완료, 합계 {len(all_faces)}개의 얼굴 검출.")
        non_max_suppressed_faces, _ = self.non_max_suppression(np.array(all_faces), np.ones(len(all_faces)), 0.6)
        logging.info(f"비 최대 억제 후, {len(non_max_suppressed_faces)}개의 얼굴 검출.")
        #
        return non_max_suppressed_faces
        #
    #
    # 비 최대 억제 함수
    @staticmethod
    def non_max_suppression(boxes, scores, overlapThresh):
        #
        if len(boxes) == 0:
            return [], []
            #
        #
        boxes = boxes.astype("float")
        pick = []
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        #
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(scores)
        #
        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
            #
            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])
            #
            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)
            #
            overlap = (w * h) / area[idxs[:last]]
            #
            idxs = np.delete(idxs, np.concatenate(([last], np.where(overlap > overlapThresh)[0])))
            #
        #
        return boxes[pick].astype("int"), scores[pick]
        #
    #
#
# =========================
# 추상화: 예측기 인터페이스
# =========================
class Predictor(ABC):
    @abstractmethod
    def predict(self, face_image):
        pass
        #
    #
#
# =========================
# Age, Gender, Race Predictor 구현 - SRP 및 다형성
# =========================
class FairFacePredictor(Predictor):
    def __init__(self, model_path):
        #
        self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
        self.model = self._load_model(model_path)
        #
    #
    def _load_model(self, model_path):
        #
        logging.info(f"FairFace 모델 load 중:\n{model_path}")
        model = models.resnet34(pretrained=True)
        model.fc = nn.Linear(model.fc.in_features, 18)
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model = model.to(self.device)
        model.eval()
        logging.info("FairFace 모델 load 완료")
        #
        return model
        #
    #
    def predict(self, face_image):
        #
        trans = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])
        #
        try:
            face_image = trans(face_image).unsqueeze(0).to(self.device)
        except ValueError:
            logging.error("이미지가 너무 작거나 손상됨, 예측 건너뜀.")
            return None, None, None
            #
        #
        with torch.no_grad():
            outputs = self.model(face_image).cpu().numpy().squeeze()
            #
        #
        race_pred = np.argmax(outputs[:4])
        gender_pred = np.argmax(outputs[7:9])
        age_pred = np.argmax(outputs[9:18])
        #
        race_text = ['백인', '흑인', '아시아', '중동'][race_pred]
        gender_text, box_color = [('남성', (255, 100, 50)), ('여성', (50, 100, 255))][gender_pred]
        age_text = ['영아', '유아', '10대', '20대', '30대', '40대', '50대', '60대', '70+'][age_pred]
        #
        return race_text, gender_text, box_color, age_text
        #
    #
#
# =========================
# 이미지 전처리 및 유틸리티 클래스 - SRP 및 캡슐화
# =========================
class ImageProcessor:
    #
    # 이미지 리사이즈 및 패딩 함수
    @staticmethod
    def resize_and_pad(image, target_size):
        #
        h, w, _ = image.shape
        scale = target_size / max(h, w)
        resized_img = cv2.resize(image, (int(w * scale), int(h * scale)))
        #
        delta_w = target_size - resized_img.shape[1]
        delta_h = target_size - resized_img.shape[0]
        top, bottom = delta_h // 2, delta_h - (delta_h // 2)
        left, right = delta_w // 2, delta_w - (delta_w // 2)
        #
        color = [0, 0, 0]
        new_img = cv2.copyMakeBorder(resized_img, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color)
        #
        return new_img, scale, top, left
        #
    #
    @staticmethod
    # 한글 텍스트 그리기 함수
    def draw_text_korean(image, text, position, font_size, font_color=(255, 255, 255), background_color=(0, 0, 0)):
        #
        font_path = config['font_path']
        #
        # 텍스트가 없으면 이미지 그대로 반환
        if text == '':
            return image
            #
        #
        font = ImageFont.truetype(font_path, int(font_size))
        img_pil = Image.fromarray(image)
        draw = ImageDraw.Draw(img_pil)
        #
        # 텍스트 크기 측정
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        #
        # 텍스트에 맞춰 박스 크기 조정
        box_x0 = position[0] - 5
        box_y0 = position[1] - 5
        box_x1 = position[0] + text_width + 5
        box_y1 = position[1] + text_height + 5
        #
        # 이미지가 텍스트를 수용할 수 있도록 크기를 확장
        if box_x1 > image.shape[1] or box_y1 > image.shape[0]:
            new_width = max(box_x1, image.shape[1])
            new_height = max(box_y1, image.shape[0])
            extended_img = np.ones((new_height, new_width, 3), dtype=np.uint8) * 0  # 흰색 배경
            extended_img[:image.shape[0], :image.shape[1]] = image
            img_pil = Image.fromarray(extended_img)
            draw = ImageDraw.Draw(img_pil)
            #
        #
        # 배경 박스 그리기
        draw.rectangle([box_x0, box_y0, box_x1, box_y1], fill=background_color)
        #
        # 텍스트 그리기
        draw.text(position, text, font=font, fill=font_color)
        #
        return np.array(img_pil)
        #
    #
    @staticmethod
    # 이미지 확장 및 텍스트 추가 함수 (위쪽 확장)
    def extend_and_add_text_above(image, text, font_size, font_color=(255, 255, 255), background_color=(0, 0, 0)):
        #
        font_path = config['font_path']
        # 이미지 크기 가져오기
        height, width, _ = image.shape
        #
        # 텍스트 크기 계산
        font = ImageFont.truetype(font_path, font_size)
        line_spacing = int(font_size * 1.5)
        text_lines = text.count('\n') + 1
        total_text_height = line_spacing * text_lines
        #
        # 새 이미지 생성 (텍스트를 위한 공간 + 원본 이미지)
        extended_image = np.zeros((height + total_text_height + 20, width, 3), dtype=np.uint8)  # 검은색 배경
        extended_image[total_text_height + 20:, 0:width] = image
        #
        # 텍스트 추가
        extended_image_pil = Image.fromarray(extended_image)
        draw = ImageDraw.Draw(extended_image_pil)
        draw.rectangle([(0, 0), (width, total_text_height + 20)], fill=background_color)
        draw.text((10, 10), text, font=font, fill=font_color)
        #
        return np.array(extended_image_pil)
        #
    #
#
# =========================
# 이미지 메타데이터 관리자 클래스 - SRP 및 캡슐화
# =========================
class ImageMetadataManager:
    @staticmethod
    def copy_and_modify_image(image_path, output_folder):
        # 출력 폴더 생성
        os.makedirs(output_folder, exist_ok=True)
        # output_folder 경로에 이미지 복사
        shutil.copy(image_path, output_folder)
        # 복사된 이미지 경로
        copied_image_path = os.path.join(output_folder, os.path.basename(image_path))
        #
        # 복사된 이미지 연 후 메타데이터 추가
        with Image.open(copied_image_path) as meta_im:
            if meta_im.mode == 'RGBA':
                meta_im = meta_im.convert('RGB')
                #
            #
            thumb_im = meta_im.copy()
            o = io.BytesIO()
            thumb_im.thumbnail((50, 50), Image.Resampling.LANCZOS)
            thumb_im.save(o, "jpeg")
            thumbnail = o.getvalue()
            #
            zeroth_ifd = {
                piexif.ImageIFD.Make: u"oldcamera",
                piexif.ImageIFD.XResolution: (96, 1),
                piexif.ImageIFD.YResolution: (96, 1),
                piexif.ImageIFD.Software: u"piexif",
                piexif.ImageIFD.Artist: u"0!code",
            }
            #
            exif_ifd = {
                piexif.ExifIFD.DateTimeOriginal: u"2099:09:29 10:10:10",
                piexif.ExifIFD.LensMake: u"LensMake",
                piexif.ExifIFD.Sharpness: 65535,
                piexif.ExifIFD.LensSpecification: ((1, 1), (1, 1), (1, 1), (1, 1)),
            }
            #
            gps_ifd = {
                piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
                piexif.GPSIFD.GPSAltitudeRef: 1,
                piexif.GPSIFD.GPSDateStamp: u"1999:99:99 99:99:99",
            }
            #
            first_ifd = {
                piexif.ImageIFD.Make: u"oldcamera",
                piexif.ImageIFD.XResolution: (40, 1),
                piexif.ImageIFD.YResolution: (40, 1),
                piexif.ImageIFD.Software: u"piexif"
            }
            #
            exif_dict = {"0th": zeroth_ifd, "Exif": exif_ifd, "GPS": gps_ifd, "1st": first_ifd, "thumbnail": thumbnail}
            exif_bytes = piexif.dump(exif_dict)
            #
            meta_im.save(copied_image_path, exif=exif_bytes)
            logging.info(f"이미지가 저장되었습니다. {copied_image_path}")
            #
        #
    #
    @staticmethod
    def print_exif_data(image_path):
        #
        with Image.open(image_path) as im:
            exif_data = piexif.load(im.info['exif'])
            print(exif_data)
            #
        #
    #
#
# =========================
# 얼굴 인식 시스템 클래스 - SRP, OCP, DIP 적용
# =========================
class FaceRecognitionSystem:
    def __init__(self, detector_manager: FaceDetectionManager, predictor: Predictor, image_processor: ImageProcessor, metadata_manager: ImageMetadataManager):
        #
        self.detector_manager = detector_manager
        self.predictor = predictor
        self.image_processor = image_processor
        self.metadata_manager = metadata_manager
        #
    #
    def process_image(self, image_path, target_encodings):
        #
        # 초기화
        cnt = 1
        predictions = []
        face_cnt = 0
        race_cnt = {'백인': 0, '흑인': 0, '아시아': 0, '중동': 0}
        male_cnt = 0
        #
        image = cv2.imread(image_path)
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        #
        # 얼굴 검출 (리사이즈 전에 수행)
        faces = self.detector_manager.detect_faces(image, image_path)  # 각각의 얼굴들이 모인 리스트
        font_size = max(12, int(image_rgb.shape[1] / 200))  # 이미지 크기에 따라 폰트 크기 조정
        #
        # 각 얼굴들을 순회
        for face in faces:
            #
            x, y, x2, y2 = face
            face_width = x2 - x
            face_height = y2 - y
            #
            face_image = image_rgb[y:y2, x:x2]
            #
            encodings = face_recognition.face_encodings(image_rgb, [(y, x + face_width, y + face_height, x)])  # 얼굴 인코딩
            #
            if not encodings:
                continue
                #
            #
            gaka = any(face_recognition.compare_faces(target_encodings, encodings[0], tolerance=0.3))
            #
            # FairFace 모델로 나이, 성별, 인종 예측
            logging.info(f"FairFace 예측 진행 중: {cnt}번째 얼굴")
            race_text, gender_text, box_color, age_text = self.predictor.predict(face_image)
            logging.info(f"예측 완료: 인종({race_text}) 성별({gender_text}) 연령대({age_text})")
            #
            if race_text is None or gender_text is None or box_color is None or age_text is None:
                print(f"데이터가 부족하여 {x}, {y}에서 얼굴을 건너뜁니다.")
                continue
                #
            #
            race_cnt[race_text] += 1
            male_cnt += 1 if gender_text == '남성' else 0
            #
            # 얼굴이 너무 작으면 예측 스킵
            if (face_width > 10 and face_height > 10):
                #
                # 가카
                if gaka and gender_text == '남성':
                    prediction_text = f'가카!'
                    box_color = (0, 255, 0)
                    #
                else:
                    prediction_text = f"{age_text}"
                    #
            else:
                print(f"Face at {x}, {y} is too small, skipping prediction.")
                prediction_text = ""
                box_color = (0, 0, 0)
                #
            #
            predictions.append((x, y, x2 - x, y2 - y, box_color, prediction_text))
            #
            face_cnt += 1
            #
        #
        # 이미지 해상도 일관성을 위해 리사이즈 및 패딩 추가
        image_rgb, scale, top, left = self.image_processor.resize_and_pad(image_rgb, 512)
        #
        for x, y, w, h, box_color, prediction_text in predictions:
            #
            # 좌표를 리사이즈된 이미지에 맞게 조정
            x = int(x * scale) + left
            y = int(y * scale) + top
            w = int(w * scale)
            h = int(h * scale)
            #
            # 이미지에 박스 및 텍스트 추가
            image_rgb = self.image_processor.draw_text_korean(image_rgb, prediction_text, (x, y), 15, font_color=(0, 0, 0), background_color=box_color)
            image_rgb = cv2.rectangle(image_rgb, (x, y), (x + w, y + h), box_color, 2)
            #
        #
        # 사진 분석 결과 정보
        face_info = f"검출된 인원 수: {face_cnt}명\n"
        gender_info = f"남성: {male_cnt}명\n여성: {face_cnt - male_cnt}명\n"
        race_info = "\n".join([f"{race}: {count}명" for race, count in race_cnt.items() if count != 0])
        info = face_info + gender_info + race_info
        # 이미지에 텍스트 추가
        image_rgb = self.image_processor.extend_and_add_text_above(image_rgb, info, font_size=font_size)
        # 저장할 파일 경로 설정
        output_path = os.path.join(config['results_folder'], os.path.basename(image_path))
        # 이미지 저장
        cv2.imwrite(output_path, cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
        logging.info(f"이미지 분석 결과 저장:\n{output_path}")
        #
        # 가카 여부에 따라 저장 폴더 설정
        detection_folder = "detection_target" if gaka else "detection_non_target"
        output_folder = os.path.join(config['results_folder'], f'{detection_folder}')
        # 이미지 저장 및 메타데이터 추가
        self.metadata_manager.copy_and_modify_image(image_path, output_folder)
        logging.info(f"메타데이터 추가 이미지 저장:\n{output_folder}")
        #
    #
#
# =========================
# 메인 실행 모듈
# =========================
def main():
    #
    # 얼굴 탐지기, 예측기, 이미지 프로세서, 메타데이터 관리자 생성
    detector_manager = FaceDetectionManager([
        DlibFaceDetector(config['dlib_model_path']),
        YOLOFaceDetector(config['yolo_model_path']),
        MTCNNFaceDetector()
    ])
    #
    # 얼굴 예측기 생성
    predictor = FairFacePredictor(config['fair_face_model_path'])
    #
    # 이미지 프로세서, 메타데이터 관리자 생성
    image_processor = ImageProcessor()
    metadata_manager = ImageMetadataManager()
    #
    # 얼굴 인식 시스템 생성
    face_recognition_system = FaceRecognitionSystem(detector_manager, predictor, image_processor, metadata_manager)
    #
    # 타겟 얼굴 인코딩 load
    with open(config['pickle_path'], 'rb') as f:
        target_encodings = np.array(pickle.load(f))
        #
    #
    # 이미지 폴더에서 이미지 load
    image_list = [f for f in os.listdir(config['image_folder']) if f.lower().endswith(('png', 'jpg', 'jpeg'))]
    #
    for image in random.sample(image_list, 1):
        image_path = os.path.join(config['image_folder'], image)
        logging.info(f"이미지 처리 시작:\n{image_path}")
        face_recognition_system.process_image(image_path, target_encodings)
        logging.info("이미지 처리 완료")
        #
    #
#
if __name__ == "__main__":
    #
    base_drive_dir = Path(os.getcwd())
    #
    # 경로는 전역 변수
    config = {
        "dlib_model_path"       : os.path.join(base_drive_dir, r'Model\DilbCNN\mmod_human_face_detector.dat'),
        "landmark_path"         : os.path.join(base_drive_dir, r'Model\DlibCNN\shape_predictor_68_face_landmarks.dat'),
        "yolo_model_path"       : os.path.join(base_drive_dir, r'Model\YOLOv8\yolov8n-face.pt'),
        "fair_face_model_path"  : os.path.join(base_drive_dir, r'FairFace\resnet34_fair_face_4.pt'),
        "image_folder"          : os.path.join(base_drive_dir, r'Image\test\test_park_mind_problem'),
        "pickle_path"           : os.path.join(base_drive_dir, r'Embedings\FaceRecognition(ResNet34).pkl'),
        "results_folder"        : os.path.join(base_drive_dir, r'results'),
        "font_path"             : os.path.join(base_drive_dir, r'fonts\NanumGothic.ttf'),
    }
    #
    main()
    #
#