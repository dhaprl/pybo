import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import shutil
import io
import piexif
import logging
import warnings
import pickle
import torch
import torch.nn as nn
from torchvision import models, transforms
from mtcnn import MTCNN
from abc import ABC, abstractmethod
from pathlib import Path
import face_recognition

# 이미지 처리 함수들 (이전 답변에서 리팩토링된 함수들)
def calculate_scale(image_shape, target_size):
    h, w = image_shape[:2]
    return target_size / max(h, w)

def resize_image(image, scale):
    h, w = image.shape[:2]
    new_w, new_h = int(w * scale), int(h * scale)
    return cv2.resize(image, (new_w, new_h))

def add_padding(image, target_size, padding_color=(0, 0, 0)):
    delta_w = target_size - image.shape[1]
    delta_h = target_size - image.shape[0]
    top = delta_h // 2
    bottom = delta_h - top
    left = delta_w // 2
    right = delta_w - left
    padded_img = cv2.copyMakeBorder(
        image, top, bottom, left, right, cv2.BORDER_CONSTANT, value=padding_color
    )
    return padded_img, top, left

def resize_image_with_padding(image, target_size, padding_color=(0, 0, 0)):
    scale = calculate_scale(image.shape, target_size)
    resized_img = resize_image(image, scale)
    new_img, top, left = add_padding(resized_img, target_size, padding_color)
    return new_img, scale, top, left

def measure_text_size(text, font):
    """텍스트 크기 측정"""
    dummy_img = Image.new('RGB', (1, 1))
    draw = ImageDraw.Draw(dummy_img)
    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]
    return text_width, text_height

def calculate_text_box(position, text_size, padding=5):
    """텍스트 박스 위치 계산"""
    x, y = position
    text_width, text_height = text_size
    return (
        x - padding,
        y - padding,
        x + text_width + padding,
        y + text_height + padding,
    )


def extend_image_if_needed(image, new_size, background_color=(0, 0, 0)):
    new_width, new_height = new_size
    height, width = image.shape[:2]
    if new_width > width or new_height > height:
        extended_img = np.full(
            (max(height, new_height), max(width, new_width), 3),
            background_color,
            dtype=np.uint8,
        )
        extended_img[:height, :width] = image
        return extended_img
    return image


def draw_korean_text(
    config,
    image,
    text,
    position,
    font_size,
    font_color=(255, 255, 255),
    background_color=(0, 0, 0),
):
    """이미지에 한글 텍스트 그리기"""
    if not text:
        return image

    font_path = config['font_path']
    font = ImageFont.truetype(font_path, font_size)
    text_size = measure_text_size(text, font)
    box_coords = calculate_text_box(position, text_size)
    image = extend_image_if_needed(
        image, (box_coords[2], box_coords[3]), background_color
    )
    image_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(image_pil)
    draw.rectangle(box_coords, fill=background_color)
    draw.text(position, text, font=font, fill=font_color)
    return np.array(image_pil)

def draw_korean_text(
    config,
    image,
    text,
    position,
    font_size,
    font_color=(255, 255, 255),
    background_color=(0, 0, 0),
):
    if not text:
        return image

    font_path = config['font_path']
    font = ImageFont.truetype(font_path, font_size)
    text_size = measure_text_size(text, font)
    box_coords = calculate_text_box(position, text_size)
    image = extend_image_if_needed(
        image, (box_coords[2], box_coords[3]), background_color
    )
    image_pil = Image.fromarray(image)
    draw = ImageDraw.Draw(image_pil)
    draw.rectangle(box_coords, fill=background_color)
    draw.text(position, text, font=font, fill=font_color)
    return np.array(image_pil)

def calculate_total_text_height(text, font_size):
    lines = text.split('\n')
    line_height = font_size * 1.5
    return int(line_height * len(lines) + 20)  # 여백 포함

def create_extended_image(image, extra_height, background_color=(0, 0, 0)):
    height, width = image.shape[:2]
    extended_img = np.full(
        (height + extra_height, width, 3), background_color, dtype=np.uint8
    )
    extended_img[extra_height:, :] = image
    return extended_img

def extend_image_with_text(
    config,
    image,
    text,
    font_size,
    font_color=(255, 255, 255),
    background_color=(0, 0, 0),
):
    font_path = config['font_path']
    extra_height = calculate_total_text_height(text, font_size)
    extended_image = create_extended_image(image, extra_height, background_color)
    extended_image = draw_text_on_image(
        extended_image, text, (10, 10), font_path, font_size, font_color
    )
    return extended_image

def copy_image_to_folder(image_path, output_folder):
    os.makedirs(output_folder, exist_ok=True)
    shutil.copy(image_path, output_folder)
    return os.path.join(output_folder, os.path.basename(image_path))

def add_metadata_to_image(image_path):
    with Image.open(image_path) as meta_im:
        if meta_im.mode == 'RGBA':
            meta_im = meta_im.convert('RGB')

        thumb_io = io.BytesIO()
        meta_im.thumbnail((50, 50), Image.Resampling.LANCZOS)
        meta_im.save(thumb_io, "jpeg")
        thumbnail = thumb_io.getvalue()

        zeroth_ifd = {
            piexif.ImageIFD.Make: u"oldcamera",
            piexif.ImageIFD.XResolution: (96, 1),
            piexif.ImageIFD.YResolution: (96, 1),
            piexif.ImageIFD.Software: u"piexif",
            piexif.ImageIFD.Artist: u"0!code",
        }

        exif_ifd = {
            piexif.ExifIFD.DateTimeOriginal: u"2099:09:29 10:10:10",
            piexif.ExifIFD.LensMake: u"LensMake",
            piexif.ExifIFD.Sharpness: 65535,
            piexif.ExifIFD.LensSpecification: (
                (1, 1),
                (1, 1),
                (1, 1),
                (1, 1),
            ),
        }

        gps_ifd = {
            piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
            piexif.GPSIFD.GPSAltitudeRef: 1,
            piexif.GPSIFD.GPSDateStamp: u"1999:99:99 99:99:99",
        }

        first_ifd = {
            piexif.ImageIFD.Make: u"oldcamera",
            piexif.ImageIFD.XResolution: (40, 1),
            piexif.ImageIFD.YResolution: (40, 1),
            piexif.ImageIFD.Software: u"piexif",
        }

        exif_dict = {
            "0th": zeroth_ifd,
            "Exif": exif_ifd,
            "GPS": gps_ifd,
            "1st": first_ifd,
            "thumbnail": thumbnail,
        }
        exif_bytes = piexif.dump(exif_dict)
        meta_im.save(image_path, exif=exif_bytes)

def copy_image_and_add_metadata(image_path, output_folder):
    copied_image_path = copy_image_to_folder(image_path, output_folder)
    add_metadata_to_image(copied_image_path)
    logging.info(f"이미지가 저장되었습니다: {copied_image_path}")

def draw_rectangle(image, coordinates, color, thickness):
    x, y, w, h = coordinates
    cv2.rectangle(image, (x, y), (x + w, y + h), color, thickness)

def draw_face_boxes(image, faces, color=(0, 255, 0), thickness=2):
    for face in faces:
        draw_rectangle(image, face, color, thickness)

# 경고 및 로깅 설정 함수
def setup_warnings_and_logging():
    warnings.filterwarnings("ignore")
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[logging.StreamHandler()]
    )

# 추상화: AI Model 인터페이스
class AIModel(ABC):
    @abstractmethod
    def __init__(self, model_path):
        pass

    @abstractmethod
    def predict(self, image, image_path=None):
        pass

# Dlib 모델 Face Detector 구현
class DlibFaceDetector(AIModel):
    def __init__(self, model_path):
        try:
            import dlib
            logging.info(f"Dlib 모델 로드 중: {model_path}")
            self.detector = dlib.cnn_face_detection_model_v1(model_path)
        except FileNotFoundError:
            logging.error(f"Dlib 모델 파일을 찾을 수 없습니다: {model_path}")
            self.detector = None
        except Exception as e:
            logging.error(f"Dlib 모델 로드 중 오류 발생: {e}")
            self.detector = None

    def predict(self, image, image_path=None):
        if self.detector is None:
            logging.error("Dlib 모델이 로드되지 않았습니다.")
            return []
        detections = self.detector(image, 1)
        faces = [
            (d.rect.left(), d.rect.top(), d.rect.right(), d.rect.bottom())
            for d in detections
        ]
        return faces

# YOLO 모델 Face Detector 구현
class YOLOFaceDetector(AIModel):
    def __init__(self, model_path):
        try:
            from ultralytics import YOLO
            logging.info(f"YOLO 모델 로드 중: {model_path}")
            self.detector = YOLO(model_path)
        except FileNotFoundError:
            logging.error(f"YOLO 모델 파일을 찾을 수 없습니다: {model_path}")
            self.detector = None
        except Exception as e:
            logging.error(f"YOLO 모델 로드 중 오류 발생: {e}")
            self.detector = None

    def predict(self, image, image_path=None):
        if self.detector is None:
            logging.error("YOLO 모델이 로드되지 않았습니다.")
            return []
        if image_path is None:
            logging.error("YOLOFaceDetector는 이미지 경로를 필요로 합니다.")
            return []
        results = self.detector.predict(image_path, conf=0.35, imgsz=1280, max_det=1000)
        faces = [
            (
                int(box.xyxy[0][0]),
                int(box.xyxy[0][1]),
                int(box.xyxy[0][2]),
                int(box.xyxy[0][3])
            )
            for result in results for box in result.boxes
        ]
        return faces

# MTCNN 모델 Face Detector 구현
class MTCNNFaceDetector(AIModel):
    def __init__(self, model_path=None):
        try:
            logging.info("MTCNN 모델 로드 중...")
            self.detector = MTCNN()
        except Exception as e:
            logging.error(f"MTCNN 모델 로드 중 오류 발생: {e}")
            self.detector = None

    def predict(self, image, image_path=None):
        if self.detector is None:
            logging.error("MTCNN 모델이 로드되지 않았습니다.")
            return []
        detections = self.detector.detect_faces(image)
        faces = [
            (
                f['box'][0],
                f['box'][1],
                f['box'][0] + f['box'][2],
                f['box'][1] + f['box'][3]
            )
            for f in detections
        ]
        return faces

# FairFace 모델 Face Predictor 구현
class FairFacePredictor(AIModel):
    def __init__(self, model_path):
        try:
            self.device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")
            logging.info(f"FairFace 모델 로드 중: {model_path}")
            model = models.resnet34(pretrained=True)
            model.fc = nn.Linear(model.fc.in_features, 18)
            model.load_state_dict(torch.load(model_path, map_location=self.device))
            self.model = model.to(self.device).eval()
            logging.info("FairFace 모델 로드 완료")
        except Exception as e:
            logging.error(f"FairFace 모델 로드 중 오류 발생: {e}")
            self.model = None

    def predict(self, image, image_path=None):
        if self.model is None:
            logging.error("FairFace 모델이 로드되지 않았습니다.")
            return None

        trans = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
        ])

        try:
            face_image = trans(image).unsqueeze(0).to(self.device)
        except ValueError:
            logging.error("이미지가 너무 작거나 손상됨, 예측 건너뜀.")
            return None

        with torch.no_grad():
            outputs = self.model(face_image).cpu().numpy().squeeze()

        race_pred = np.argmax(outputs[:4])
        gender_pred = np.argmax(outputs[7:9])
        age_pred = np.argmax(outputs[9:18])

        race_text = ['백인', '흑인', '아시아', '중동'][race_pred]
        gender_text, box_color = [('남성', (50, 100, 255)), ('여성', (255, 100, 50))][gender_pred]
        age_text = ['영아', '유아', '10대', '20대', '30대', '40대', '50대', '60대', '70+'][age_pred]

        return {
            "race": race_text,
            "gender": gender_text,
            "box_color": box_color,
            "age": age_text
        }

# 추상화: Model 관리자 클래스
class ModelManager(ABC):
    @abstractmethod
    def __init__(self, *args):
        pass

    @abstractmethod
    def manage_prediction(self, image, image_path=None):
        pass

# FaceDetector 관리자 클래스
class FaceDetectors(ModelManager):
    def __init__(self, *detectors):
        self.detectors = detectors

    def manage_prediction(self, image, image_path=None):
        logging.info("얼굴 탐지 시작...")
        all_faces = []
        for detector in self.detectors:
            try:
                if isinstance(detector, YOLOFaceDetector) and image_path:
                    faces = detector.predict(image, image_path)
                else:
                    faces = detector.predict(image)
                logging.info(f"{detector.__class__.__name__}: {len(faces)}개의 얼굴 검출")
                all_faces.extend(faces)
            except Exception as e:
                logging.error(f"{detector.__class__.__name__} 탐지 중 오류 발생: {e}")
        logging.info(f"총 {len(all_faces)}개의 얼굴 검출.")
        return self._apply_non_max_suppression(all_faces)

    @staticmethod
    def _apply_non_max_suppression(faces):
        if len(faces) == 0:
            return []
        boxes = np.array(faces).astype("float")
        pick = []
        x1 = boxes[:, 0]
        y1 = boxes[:, 1]
        x2 = boxes[:, 2]
        y2 = boxes[:, 3]
        area = (x2 - x1 + 1) * (y2 - y1 + 1)
        idxs = np.argsort(y2)
        while len(idxs) > 0:
            last = len(idxs) - 1
            i = idxs[last]
            pick.append(i)
            xx1 = np.maximum(x1[i], x1[idxs[:last]])
            yy1 = np.maximum(y1[i], y1[idxs[:last]])
            xx2 = np.minimum(x2[i], x2[idxs[:last]])
            yy2 = np.minimum(y2[i], y2[idxs[:last]])
            w = np.maximum(0, xx2 - xx1 + 1)
            h = np.maximum(0, yy2 - yy1 + 1)
            overlap = (w * h) / area[idxs[:last]]
            idxs = np.delete(
                idxs, np.concatenate(([last], np.where(overlap > 0.3)[0]))
            )
        return boxes[pick].astype("int").tolist()

# FacePredictor 관리자 클래스
class FacePredictors(ModelManager):
    def __init__(self, *predictors):
        self.predictors = predictors

    def manage_prediction(self, face_image):
        logging.info("얼굴 예측 시작...")
        all_predictions = {}
        for predictor in self.predictors:
            try:
                prediction = predictor.predict(face_image)
                if prediction:
                    all_predictions.update(prediction)
            except Exception as e:
                logging.error(f"{predictor.__class__.__name__} 예측 중 오류 발생: {e}")
        logging.info(f"예측 결과: {all_predictions}")
        return all_predictions

# 얼굴 인식 시스템 클래스
class AiSystem:
    def __init__(self, config, detector_manager, predictor_manager):
        self.config = config
        self.detector_manager = detector_manager
        self.predictor_manager = predictor_manager

    def process_image(self, image_path, target_encodings):
        try:
            image_rgb, faces = self._detect_faces(image_path)
            predictions, face_cnt, race_cnt, male_cnt = self._compile_predictions(
                image_rgb, faces, target_encodings
            )
            result_image = self._draw_results(
                image_rgb, predictions, face_cnt, male_cnt, race_cnt
            )
            self._save_results(image_path, result_image, predictions)
        except Exception as e:
            logging.error(f"이미지 처리 중 오류 발생: {e}")

    def _detect_faces(self, image_path):
        try:
            image = cv2.imread(image_path)
            if image is None:
                raise ValueError(f"이미지를 읽을 수 없습니다: {image_path}")
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
            faces = self.detector_manager.manage_prediction(image_rgb, image_path)
            logging.info(f"얼굴 탐지 완료: {len(faces)}명")
            return image_rgb, faces
        except Exception as e:
            logging.error(f"얼굴 탐지 중 오류 발생: {e}")
            raise

    def _compile_predictions(self, image_rgb, faces, target_encodings):
        predictions = []
        face_cnt = 0
        race_cnt = {'백인': 0, '흑인': 0, '아시아': 0, '중동': 0}
        male_cnt = 0
        for face in faces:
            prediction = self._predict_face(image_rgb, face, target_encodings)
            if prediction:
                predictions.append(prediction)
                face_cnt += 1
                race_text, gender_text = prediction[4], prediction[5]
                race_cnt[race_text] += 1
                if gender_text == '남성':
                    male_cnt += 1
        return predictions, face_cnt, race_cnt, male_cnt

    def _predict_face(self, image_rgb, face, target_encodings):
        try:
            x, y, x2, y2 = face
            face_image = image_rgb[y:y2, x:x2]
            encodings = face_recognition.face_encodings(
                image_rgb, [(y, x2, y2, x)]
            )
            if not encodings:
                logging.warning(f"얼굴 인코딩 실패: {face}")
                return None
            prediction_result = self.predictor_manager.manage_prediction(face_image)
            if not prediction_result:
                return None
            race_text = prediction_result.get("race", "알 수 없음")
            gender_text = prediction_result.get("gender", "알 수 없음")
            box_color = prediction_result.get("box_color", (0, 0, 0))
            age_text = prediction_result.get("age", "알 수 없음")
            is_target = any(
                face_recognition.compare_faces(target_encodings, encodings[0], tolerance=0.3)
            )
            prediction_text = '가카!' if is_target and gender_text == '남성' else age_text
            return x, y, x2 - x, y2 - y, race_text, gender_text, box_color, prediction_text
        except Exception as e:
            logging.error(f"단일 얼굴 처리 중 오류 발생: {e}")
            return None

    def _draw_results(self, image_rgb, predictions, face_cnt, male_cnt, race_cnt):
        font_size = max(12, int(image_rgb.shape[1] / 200))
        image_rgb, scale, top, left = resize_image_with_padding(image_rgb, 512)
        for x, y, w, h, _, _, box_color, prediction_text in predictions:
            x = int(x * scale) + left
            y = int(y * scale) + top
            w = int(w * scale)
            h = int(h * scale)
            image_rgb = draw_korean_text(
                self.config,
                image_rgb,
                prediction_text,
                (x, y),
                15,
                font_color=(0, 0, 0),
                background_color=box_color
            )
            draw_rectangle(image_rgb, (x, y, w, h), box_color, 2)
        info_text = f"검출된 인원 수: {face_cnt}명\n남성: {male_cnt}명\n여성: {face_cnt - male_cnt}명\n"
        race_info = "\n".join(
            [f"{race}: {count}명" for race, count in race_cnt.items() if count > 0]
        )
        image_rgb = extend_image_with_text(
            self.config, image_rgb, info_text + race_info, font_size
        )
        return image_rgb

    def _save_results(self, image_path, image_rgb, predictions):
        try:
            output_path = os.path.join(
                self.config['results_folder'], os.path.basename(image_path)
            )
            cv2.imwrite(output_path, cv2.cvtColor(image_rgb, cv2.COLOR_RGB2BGR))
            logging.info(f"이미지 분석 결과 저장: {output_path}")
            target_detected = any("가카" in pred[7] for pred in predictions)
            detection_folder = (
                "detection_target" if target_detected else "detection_non_target"
            )
            output_folder = os.path.join(
                self.config['results_folder'], detection_folder
            )
            copy_image_and_add_metadata(image_path, output_folder)
            logging.info(f"메타데이터 추가된 이미지 저장: {output_folder}")
        except Exception as e:
            logging.error(f"결과 저장 중 오류 발생: {e}")

# Django 시스템 설정 데코레이터
def setup_django_system(func):
    def wrapper(request, image_path, *args, **kwargs):
        setup_warnings_and_logging()
        base_dir = os.path.join(Path(__file__).resolve().parent, 'ai_files')
        django_media_dir = os.path.join(
            Path(__file__).resolve().parent.parent.parent, 'media/pybo/answer_image'
        )
        config = {
            "dlib_model_path": os.path.join(base_dir, 'ai_models', 'DilbCNN', 'mmod_human_face_detector.dat'),
            "yolo_model_path": os.path.join(base_dir, 'ai_models', 'YOLOv8', 'yolov8n-face.pt'),
            "fair_face_model_path": os.path.join(base_dir, 'ai_models', 'FairFace', 'resnet34_fair_face_4.pt'),
            "image_folder": os.path.join(base_dir, 'image_test', 'test_park_mind_problem'),
            "pickle_path": os.path.join(base_dir, 'embedings', 'FaceRecognition(ResNet34).pkl'),
            "font_path": os.path.join(base_dir, 'fonts', 'NanumGothic.ttf'),
            "results_folder": django_media_dir,
        }
        selected_detectors = request.POST.getlist('detectors')
        selected_predictors = request.POST.getlist('predictors')
        detectors = []
        if 'dlib' in selected_detectors:
            detectors.append(DlibFaceDetector(config['dlib_model_path']))
        if 'yolo' in selected_detectors:
            detectors.append(YOLOFaceDetector(config['yolo_model_path']))
        if 'mtcnn' in selected_detectors:
            detectors.append(MTCNNFaceDetector())
        if not detectors:
            logging.warning("탐지기가 선택되지 않았습니다. 탐지 작업을 건너뜁니다.")
            detector_manager = None
        else:
            detector_manager = FaceDetectors(*detectors)
        predictors = []
        if 'fairface' in selected_predictors:
            predictors.append(FairFacePredictor(config['fair_face_model_path']))
        if not predictors:
            logging.warning("예측기가 선택되지 않았습니다. 예측 작업을 건너뜁니다.")
            predictor_manager = None
        else:
            predictor_manager = FacePredictors(*predictors)
        ai_system = ForDjango(config, detector_manager, predictor_manager)
        with open(config['pickle_path'], 'rb') as f:
            target_encodings = np.array(pickle.load(f))
        return func(request, image_path, ai_system, target_encodings, *args, **kwargs)
    return wrapper

# 얼굴 인식 시스템 클래스 for Django
class ForDjango(AiSystem):
    def __init__(self, config, detector_manager, predictor_manager):
        super().__init__(config, detector_manager, predictor_manager)

    def process_image(self, image_path, target_encodings):
        try:
            image_rgb, faces = self._detect_faces(image_path)
            if self.predictor_manager:
                predictions, face_cnt, race_cnt, male_cnt = self._compile_predictions(
                    image_rgb, faces, target_encodings
                )
            else:
                predictions = faces
                face_cnt = len(faces)
                race_cnt = None
                male_cnt = None
            result_image = self._draw_results(
                image_rgb, predictions, face_cnt, male_cnt, race_cnt
            )
            output_path = self._save_results(image_path, result_image, predictions)
            logging.info(f"이미지 분석 결과 저장: {output_path}")
            django_path = os.path.join('pybo/answer_image', os.path.basename(output_path))
            return django_path
        except Exception as e:
            logging.error(f"이미지 처리 중 오류 발생: {e}")

    def _draw_results(self, image_rgb, predictions, face_cnt, male_cnt, race_cnt):
        font_size = max(12, int(image_rgb.shape[1] / 200))
        image_rgb, scale, top, left = resize_image_with_padding(image_rgb, 512)
        try:
            for x, y, w, h, _, _, box_color, _ in predictions:
                x = int(x * scale) + left
                y = int(y * scale) + top
                w = int(w * scale)
                h = int(h * scale)
                draw_rectangle(image_rgb, (x, y, w, h), box_color, 2)
            info_text = f"검출된 인원 수: {face_cnt}명\n남성: {male_cnt}명\n여성: {face_cnt - male_cnt}명\n"
            race_info = "\n".join(
                [f"{race}: {count}명" for race, count in race_cnt.items() if count > 0]
            )
        except Exception:
            for x, y, x2, y2 in predictions:
                w, h = x2 - x, y2 - y
                x = int(x * scale) + left
                y = int(y * scale) + top
                w = int(w * scale)
                h = int(h * scale)
                draw_rectangle(image_rgb, (x, y, w, h), (0, 255, 0), 2)
            info_text = f"검출된 인원 수: {face_cnt}명\n"
            race_info = ""
        image_rgb = extend_image_with_text(
            self.config, image_rgb, info_text + race_info, font_size
        )
        return image_rgb

    def _save_results(self, image_path, result_image, predictions=None):
        os.makedirs(self.config['results_folder'], exist_ok=True)
        output_path = os.path.join(
            self.config['results_folder'], os.path.basename(image_path)
        )
        cv2.imwrite(output_path, cv2.cvtColor(result_image, cv2.COLOR_RGB2BGR))
        logging.info(f"이미지 분석 결과 저장: {output_path}")
        return output_path

# 메인 실행 모듈
def main():
    setup_warnings_and_logging()
    base_dir = os.path.join(Path(__file__).resolve().parent, 'ai_files')
    config = {
        "dlib_model_path": os.path.join(base_dir, 'ai_models', 'DilbCNN', 'mmod_human_face_detector.dat'),
        "yolo_model_path": os.path.join(base_dir, 'ai_models', 'YOLOv8', 'yolov8n-face.pt'),
        "fair_face_model_path": os.path.join(base_dir, 'ai_models', 'FairFace', 'resnet34_fair_face_4.pt'),
        "image_folder": os.path.join(base_dir, 'image_test', 'test_park_mind_problem'),
        "pickle_path": os.path.join(base_dir, 'embedings', 'FaceRecognition(ResNet34).pkl'),
        "font_path": os.path.join(base_dir, 'fonts', 'NanumGothic.ttf'),
        "results_folder": os.path.join(base_dir, 'results_test')
    }
    detector_manager = FaceDetectors(
        DlibFaceDetector(config['dlib_model_path']),
        YOLOFaceDetector(config['yolo_model_path']),
        MTCNNFaceDetector()
    )
    predictor_manager = FacePredictors(
        FairFacePredictor(config['fair_face_model_path'])
    )
    ai_system = AiSystem(config, detector_manager, predictor_manager)
    with open(config['pickle_path'], 'rb') as f:
        target_encodings = np.array(pickle.load(f))
    image_list = [
        f for f in os.listdir(config['image_folder'])
        if f.lower().endswith(('png', 'jpg', 'jpeg'))
    ]
    for image in image_list:
        image_path = os.path.join(config['image_folder'], image)
        logging.info(f"이미지 처리 시작: {image_path}")
        ai_system.process_image(image_path, target_encodings)
        logging.info(f"이미지 처리 완료: {image_path}")

if __name__ == "__main__":
    main()
