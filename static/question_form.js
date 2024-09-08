//임시 파일 입니다

$(document).ready(function() {
    const modal = $('#uploadModal');
    const uploadBtn = $('#uploadBtn');
    const confirmBtn = $('.confirm-btn');
    const subjectInput = $('#subject');
    const contentInput = $('#content');
    const questionForm = $('#questionForm');
    const imagePreviewContainer = $('#image-preview-container');

    const imageUploadSettings = [
        { input: '#image1', dropZone: '#drop-zone1', previewId: '#preview-image1', mainPreviewId: '#main-preview1 img' },
        { input: '#image2', dropZone: '#drop-zone2', previewId: '#preview-image2', mainPreviewId: '#main-preview2 img' }
    ];

    function setupImageUpload(inputSelector, dropZoneSelector, previewId) {
        const $dropZone = $(dropZoneSelector);
        const $fileInput = $(inputSelector);
        const $dropText = $dropZone.find('.drop-text');
        const $imagePreview = $(previewId);

        $dropZone.on('dragover', function(event) {
            event.preventDefault();
            $dropZone.addClass('hover');
        });

        $dropZone.on('dragleave', function() {
            $dropZone.removeClass('hover');
        });

        $dropZone.on('drop', function(event) {
            event.preventDefault();
            $dropZone.removeClass('hover');
            const files = event.originalEvent.dataTransfer.files;
            if (files.length > 0 && files[0].type.startsWith('image/')) {
                $fileInput[0].files = files;
                $dropText.hide();
                const reader = new FileReader();
                reader.onload = function(e) {
                    $imagePreview.attr('src', e.target.result).show();
                }
                reader.readAsDataURL(files[0]);
            }
        });

        $dropZone.on('click', function() {
            $fileInput.click();
        });

        $fileInput.on('change', function(event) {
            if (event.target.files.length > 0) {
                $dropText.hide();
                const reader = new FileReader();
                reader.onload = function(e) {
                    $imagePreview.attr('src', e.target.result).show();
                }
                reader.readAsDataURL(event.target.files[0]);
            }
        });
    }

    function checkFormValidity() {
        const subjectValid = subjectInput.val().trim() !== '';
        const contentValid = contentInput.val().trim() !== '';
        uploadBtn.prop('disabled', !(subjectValid && contentValid));
    }

    uploadBtn.on('click', function() {
        modal.css('display', 'flex');
    });

    confirmBtn.on('click', function() {
        modal.hide();

        // 모달에서 선택된 이미지 업데이트
        imageUploadSettings.forEach(setting => {
            const fileInput = $(setting.input)[0];
            const previewImg = $(setting.previewId);
            const mainPreviewImg = $(setting.mainPreviewId);

            if (fileInput.files.length > 0) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    previewImg.attr('src', e.target.result).show();
                    mainPreviewImg.attr('src', e.target.result).show();
                }
                reader.readAsDataURL(fileInput.files[0]);
            } else {
                // 파일이 없을 때 기존 이미지 유지
                const existingImgSrc = mainPreviewImg.attr('src');
                if (existingImgSrc) {
                    previewImg.attr('src', existingImgSrc).show();
                }
            }
        });
    });

    imageUploadSettings.forEach(setting => {
        setupImageUpload(setting.input, setting.dropZone, setting.previewId);
    });

    subjectInput.add(contentInput).on('input', checkFormValidity);
    checkFormValidity();

    // 폼 제출 처리
    questionForm.on('submit', function(event) {
        event.preventDefault();

        const formData = new FormData(this);

        // 이미지 파일 추가
        imageUploadSettings.forEach(setting => {
            const fileInput = $(setting.input)[0];
            if (fileInput.files.length > 0) {
                formData.append(fileInput.id, fileInput.files[0]); // image1, image2 추가
            }
        });

        const isModify = '{{ form.instance.pk|yesno:"true,false" }}';
        const questionId = '{{ form.instance.pk }}';
        const url = isModify === 'true'
            ? '{% url "pybo:question_modify" question_id=0 %}'.replace('0', questionId)
            : '{% url "pybo:question_create" %}';

        $.ajax({
            url: url,
            method: 'POST',
            data: formData,
            processData: false,
            contentType: false,
            headers: {'X-CSRFToken': '{{ csrf_token }}'},
            success: function(response) {
                window.location.href = response.redirect_url;
            },
            error: function() {
                alert('저장에 실패했습니다. 다시 시도해 주세요.');
            }
        });
    });
});

