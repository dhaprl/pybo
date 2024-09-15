# main.py

import logging
import pickle
import numpy as np
import os
from django.conf import settings

# 각 단계별 클래스를 개별적으로 임포트합니다.
from ai_system import Pipeline, Data, BaseConfig, steps, factories

class CustomConfig(BaseConfig):
    # 별도로 추가할 커스터마이징이 없으면 그대로 사용
    django_dir = settings.BASE_DIR
    results_folder = os.path.join(django_dir, 'media', 'pybo', 'ai_image')

def process_image(image_path, selected_detectors, selected_predictors):
    """
    메인 함수로, 전체 파이프라인을 구성하고 실행합니다.
    """
    # 설정 정보를 가져옵니다.
    config = CustomConfig.get_config()

    # 탐지기(detectors) 생성
    detectors = []
    
    for detector in selected_detectors:
        if detector == 'mtcnn':
            continue
        detectors.append(factories.FaceDetectorFactory.create(detector, config[f'{detector}']))
    
    # 예측기(predictors) 생성
    predictors = []
    
    for predictor in selected_predictors:
        predictors.append(factories.FacePredictorFactory.create(predictor, config[f'{predictor}']))

    # 타겟 얼굴 인코딩 로드
    with open(config['pickle_path'], 'rb') as f:
        target_encodings = np.array(pickle.load(f))

    # 파이프라인 설정
    pipeline = Pipeline()
    pipeline.add(steps.FaceDetector(detectors))                    
    pipeline.add(steps.FaceEncoder())                           
    pipeline.add(steps.TargetFaceMatcher(target_encodings))      
    pipeline.add(steps.FacePredictor(predictors))                
    pipeline.add(steps.FaceInfoCounter())                     
    pipeline.add(steps.InfoDrawer())
    if predictors:                            
        pipeline.add(steps.InfoWriter(font_size = 30))  
    # pipeline.add(steps.ImageResizer(target_size=1000))      
    pipeline.add(steps.Saver())                                 
    
    image_path
    logging.info(f"이미지 처리 시작: {image_path}")
    # 데이터 객체를 생성하여 이미지 경로를 설정합니다.
    data = Data(config, image_path)
    # 파이프라인을 실행하여 이미지를 처리합니다.
    pipeline.run(data)
    logging.info(f"이미지 처리 완료: {image_path}")
    output_image_path = data.output_image_path
    
    return output_image_path
