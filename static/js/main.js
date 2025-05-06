document.addEventListener('DOMContentLoaded', function() {
    // Медиа-модальное окно
    const mediaModal = new bootstrap.Modal(document.getElementById('mediaModal'));
    const mediaContent = document.getElementById('mediaContent');

    // Обработчик клика для изображений
    document.querySelectorAll('.media-thumbnail[data-media-type="image"]').forEach(img => {
        img.addEventListener('click', function() {
            showMediaInModal('image', this.getAttribute('data-media-src'));
        });
    });

    // Обработчик клика для кнопки открытия видео
    document.querySelectorAll('.media-open-btn[data-media-type="video"]').forEach(btn => {
        btn.addEventListener('click', function() {
            showMediaInModal('video', this.getAttribute('data-media-src'));
        });
    });

    // Функция для показа медиа в модальном окне
    function showMediaInModal(type, src) {
        mediaContent.innerHTML = '';

        if (type === 'image') {
            const img = document.createElement('img');
            img.src = src;
            img.className = 'img-fluid';
            img.alt = 'Просмотр изображения';
            mediaContent.appendChild(img);
        } else if (type === 'video') {
            const video = document.createElement('video');
            video.controls = true;
            video.autoplay = false;
            video.className = 'w-100';

            const source = document.createElement('source');
            source.src = src;
            source.type = 'video/mp4';

            video.appendChild(source);
            mediaContent.appendChild(video);
        }

        mediaModal.show();
    }

    // Закрытие модального окна очищает его содержимое
    document.getElementById('mediaModal').addEventListener('hidden.bs.modal', function() {
        mediaContent.innerHTML = '';
    });

    // Post creation form enhancements
    const postForm = document.getElementById('post-creation-form');
    if (postForm) {
        const titleInput = document.getElementById('title');
        const contentTextarea = document.getElementById('content');
        const mediaInput = document.getElementById('media');
        const titleCharCount = document.getElementById('title-char-count');
        const contentCharCount = document.getElementById('content-char-count');
        const mediaPreviewContainer = document.getElementById('media-preview-container');
        const mediaPreview = document.getElementById('media-preview');
        const removeMediaBtn = document.getElementById('remove-media');

        // Title character counter
        titleInput.addEventListener('input', function() {
            const count = this.value.length;
            titleCharCount.textContent = `${count}/100`;
            
            // Visual indication when approaching limit
            if (count > 80) {
                titleCharCount.classList.add('text-warning');
            } else {
                titleCharCount.classList.remove('text-warning');
            }
            
            if (count >= 100) {
                titleCharCount.classList.add('text-danger');
            } else {
                titleCharCount.classList.remove('text-danger');
            }
        });

        // Content character counter
        contentTextarea.addEventListener('input', function() {
            const count = this.value.length;
            contentCharCount.textContent = `${count} символов`;
        });

        // Media file preview
        mediaInput.addEventListener('change', function() {
            if (this.files && this.files[0]) {
                const file = this.files[0];
                const fileType = file.type;
                const reader = new FileReader();
                
                // Show preview container
                mediaPreviewContainer.classList.remove('d-none');
                
                reader.onload = function(e) {
                    if (fileType.startsWith('image/')) {
                        // Image preview
                        mediaPreview.innerHTML = `
                            <img src="${e.target.result}" class="img-fluid" style="max-height: 200px;" alt="Предпросмотр изображения">
                        `;
                    } else if (fileType.startsWith('video/')) {
                        // Video preview
                        mediaPreview.innerHTML = `
                            <video class="img-fluid" style="max-height: 200px;" controls>
                                <source src="${e.target.result}" type="${fileType}">
                                Ваш браузер не поддерживает видео.
                            </video>
                        `;
                    } else {
                        // Unsupported file type
                        mediaPreview.innerHTML = `
                            <div class="alert alert-warning">
                                <i class="fas fa-file me-2"></i>Файл "${file.name}" (${formatFileSize(file.size)})
                            </div>
                        `;
                    }
                };
                
                reader.readAsDataURL(file);
            } else {
                // Hide preview if no file selected
                mediaPreviewContainer.classList.add('d-none');
            }
        });

        // Remove media button
        removeMediaBtn.addEventListener('click', function() {
            mediaInput.value = '';
            mediaPreviewContainer.classList.add('d-none');
            mediaPreview.innerHTML = '';
        });

        // Format file size helper
        function formatFileSize(bytes) {
            if (bytes < 1024) return bytes + ' B';
            else if (bytes < 1048576) return (bytes / 1024).toFixed(1) + ' KB';
            else return (bytes / 1048576).toFixed(1) + ' MB';
        }
    }

    // Валидация размера файла
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const fileInput = this.querySelector('input[type="file"]');
            if (fileInput && fileInput.files.length > 0) {
                // Конвертируем предел 100 МБ в байты
                const maxSize = 100 * 1024 * 1024;

                if (fileInput.files[0].size > maxSize) {
                    e.preventDefault();
                    alert('Размер файла превышает допустимый лимит в 100 МБ.');
                }
            }
        });
    });
});