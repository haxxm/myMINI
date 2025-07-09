document.addEventListener('DOMContentLoaded', () => {
    // 1. 파일 선택 버튼 기능
    const chooseFilesBtn = document.querySelector('.choose-files-btn');
    const fileInput = document.getElementById('file-input'); // HTML에 추가된 input[type="file"]

    chooseFilesBtn.addEventListener('click', () => {
        fileInput.click(); // 버튼 클릭 시 실제 파일 입력 필드 클릭 유도
    });

    // 파일이 선택되면 자동으로 폼 제출
    // 이제는 fetch로 처리하므로 이 부분은 필요 없습니다.
    // fileInput.addEventListener('change', () => {
    //     if (fileInput.files.length > 0) {
    //         document.getElementById('upload-form').submit(); // 폼 제출
    //     }
    // });

    // 2. 드래그 앤 드롭 기능 및 파일 업로드 처리 (fetch 사용)
    const uploadArea = document.querySelector('.upload-area');
    const uploadForm = document.getElementById('upload-form'); // 폼 요소

    // 파일 입력 필드 변경 시 (CHOOSE FILES 버튼 클릭 또는 파일 선택 후)
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            handleFileUpload(fileInput.files[0]); // 첫 번째 파일만 처리
        }
    });

    // 드래그 오버 시 시각적 피드백
    uploadArea.addEventListener('dragover', (event) => {
        event.preventDefault();
        uploadArea.classList.add('drag-over');
    });

    // 드래그 나갈 때 시각적 피드백 제거
    uploadArea.addEventListener('dragleave', () => {
        uploadArea.classList.remove('drag-over');
    });

    // 파일 드롭 시 처리
    uploadArea.addEventListener('drop', (event) => {
        event.preventDefault();
        uploadArea.classList.remove('drag-over');

        const files = event.dataTransfer.files; // 드롭된 파일들
        if (files.length > 0) {
            handleFileUpload(files[0]); // 첫 번째 파일만 처리
        }
    });

    // 파일 업로드 및 서버 통신을 처리하는 함수
    function handleFileUpload(file) {
        const formData = new FormData();
        formData.append('file', file);

        // 로딩 스피너 등을 표시하는 로직 추가 가능
        // 예: showLoadingSpinner();

        fetch(uploadForm.action, {
            method: 'POST',
            body: formData
        })
        .then(response => {
            // 서버에서 리다이렉트 응답이 오면 자동으로 처리됩니다.
            // 여기서는 응답 URL을 확인하여 flash 메시지를 표시하기 위해 페이지를 새로고침합니다.
            // Flask의 flash 메시지는 리다이렉트와 함께 오므로,
            // 응답 URL로 이동하면 해당 페이지에서 flash 메시지가 렌더링됩니다.
            if (response.redirected) {
                window.location.href = response.url; // 리다이렉트된 URL로 이동
            } else {
                // 리다이렉트가 아닌 다른 응답 (예: JSON 에러 메시지)이 올 경우
                return response.json().then(data => {
                    console.error('Server response:', data);
                    alert(data.message || '파일 처리 중 알 수 없는 오류가 발생했습니다.');
                    window.location.reload();
                }).catch(() => {
                    // JSON 파싱 실패 시 일반 오류 처리
                    alert('파일 처리 중 알 수 없는 오류가 발생했습니다.');
                    window.location.reload();
                });
            }
        })
        .catch(error => {
            console.error('파일 업로드 및 변환 오류:', error);
            alert('파일 처리 중 오류가 발생했습니다.');
            window.location.reload(); // 오류 시 페이지 새로고침
        })
        .finally(() => {
            // 로딩 스피너 숨기는 로직 추가 가능
            // 예: hideLoadingSpinner();
        });
    }

    // 드롭다운 메뉴 기능 (기존 코드 유지)
    const toolsNavLink = document.querySelector('.main-nav li a');
    const dropdownMenu = document.querySelector('.main-nav .dropdown-menu');

    if (toolsNavLink && dropdownMenu) {
        toolsNavLink.addEventListener('mouseenter', () => {
            dropdownMenu.style.display = 'block';
        });

        toolsNavLink.parentNode.addEventListener('mouseleave', () => {
            dropdownMenu.style.display = 'none';
        });
    }
});
