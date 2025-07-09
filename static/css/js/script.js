document.addEventListener('DOMContentLoaded', () => {
    // 1. 파일 선택 버튼 기능
    const chooseFilesBtn = document.querySelector('.choose-files-btn');
    const fileInput = document.getElementById('file-input'); // HTML에 추가된 input[type="file"]

    chooseFilesBtn.addEventListener('click', () => {
        fileInput.click(); // 버튼 클릭 시 실제 파일 입력 필드 클릭 유도
    });

    // 파일이 선택되면 자동으로 폼 제출
    fileInput.addEventListener('change', () => {
        if (fileInput.files.length > 0) {
            document.getElementById('upload-form').submit(); // 폼 제출
        }
    });

    // 2. 드래그 앤 드롭 기능
    const uploadArea = document.querySelector('.upload-area');
    const uploadForm = document.getElementById('upload-form'); // 폼 요소

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
            // 드롭된 파일을 숨겨진 input[type="file"]에 할당
            // DataTransfer 객체를 사용하여 files 속성을 직접 설정하는 것은 보안상의 이유로 불가능합니다.
            // 따라서, 드롭된 파일을 FormData에 추가하여 직접 fetch API로 전송해야 합니다.
            // 여기서는 간단히 fileInput.files에 할당하는 대신, FormData를 직접 구성하여 제출합니다.

            const formData = new FormData();
            // 드롭된 파일이 여러 개일 경우, 첫 번째 파일만 처리하거나 모두 처리하도록 로직 변경 가능
            formData.append('file', files[0]); // 첫 번째 파일만 처리

            // fetch API를 사용하여 서버로 파일 전송
            fetch(uploadForm.action, {
                method: 'POST',
                body: formData
            })
            .then(response => {
                // 서버 응답이 파일 다운로드인 경우
                if (response.headers.get('Content-Disposition') && response.headers.get('Content-Disposition').includes('attachment')) {
                    return response.blob().then(blob => {
                        const filename = response.headers.get('Content-Disposition').split('filename=')[1].replace(/"/g, '');
                        const url = window.URL.createObjectURL(blob);
                        const a = document.createElement('a');
                        a.href = url;
                        a.download = filename;
                        document.body.appendChild(a);
                        a.click();
                        a.remove();
                        window.URL.revokeObjectURL(url);
                        alert('파일 변환 및 다운로드가 완료되었습니다!');
                        window.location.reload(); // 페이지 새로고침하여 사용 횟수 업데이트
                    });
                } else {
                    // 서버 응답이 JSON (flash 메시지 리다이렉트 등)인 경우
                    return response.text().then(text => {
                        // Flask의 flash 메시지는 HTML 리다이렉트와 함께 오므로,
                        // 페이지 전체를 새로고침하여 flash 메시지를 표시합니다.
                        window.location.href = response.url;
                    });
                }
            })
            .catch(error => {
                console.error('파일 업로드 및 변환 오류:', error);
                alert('파일 처리 중 오류가 발생했습니다.');
                window.location.reload(); // 오류 시 페이지 새로고침
            });
        }
    });

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