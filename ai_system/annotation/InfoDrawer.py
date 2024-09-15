# steps/draw_annotations_step.py

from ..core.config import PipelineStep
from ..core.utils import ImagePipeline

class InfoDrawer(PipelineStep):
    """
    얼굴 인식 결과를 이미지에 표시하는 파이프라인 단계입니다.
    """

    def process(self, data):
        """
        이미지에 얼굴 박스와 텍스트 주석을 그려넣습니다.

        Args:
            data: 파이프라인 데이터 객체.

        Returns:
            data: 주석이 추가된 이미지가 포함된 데이터 객체.
        """
        config = data.config
        pipeline = ImagePipeline(config)
        image_rgb = data.image_rgb
        predictions = data.predictions
        for index, face in enumerate(predictions['face_boxes']):
            x1, y1, x2, y2 = face # 얼굴 박스 좌표

            # 성별에 따라 박스 색상 결정 (남성: 파랑색, 여성: 빨간색)
            gender = predictions.get('gender', '남성')[index]
            box_color = (50, 100, 255) if gender == '남성' else (255, 100, 50)

            # 대상 여부에 따라 텍스트 설정
            text = '가카!' if predictions.get('is_target', [])[index] else ''

            # 이미지에 한글 텍스트 추가
            image_rgb = pipeline.draw_korean_text(
                image=image_rgb,
                text=text,
                position=(x1, y1),
                font_size=15,
                font_color=(0, 0, 0),
                background_color=box_color
            )

            # 얼굴 박스 그리기
            pipeline.draw_rectangle(image_rgb, (x1, y1, x2, y2), box_color, 2)

        # 처리된 이미지를 데이터 객체에 저장
        data.image_rgb = image_rgb
        return data
