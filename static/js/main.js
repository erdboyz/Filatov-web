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

    // Валидация размера файла
    document.querySelector('form').addEventListener('submit', function(e) {
        const fileInput = document.getElementById('media');

        if (fileInput.files.length > 0) {
            // Конвертируем предел 100 МБ в байты
            const maxSize = 100 * 1024 * 1024;

            if (fileInput.files[0].size > maxSize) {
                e.preventDefault();
                alert('Размер файла превышает допустимый лимит в 100 МБ.');
            }
        }
    });
});