document.addEventListener('DOMContentLoaded', function() {
    // Медиа-модальное окно
    const mediaModal = new bootstrap.Modal(document.getElementById('mediaModal'));
    const mediaContent = document.getElementById('mediaContent');
    const prevMediaBtn = document.getElementById('prevMediaBtn');
    const nextMediaBtn = document.getElementById('nextMediaBtn');
    
    let currentMediaIndex = 0;
    let currentPostMedia = [];

    // Setup drag overlay for the entire page
    const dragOverlay = document.querySelector('.drag-overlay');
    
    // Only setup drag events if we have a drag overlay
    if (dragOverlay) {
        // Global drag events to show overlay only when files are being dragged
        document.addEventListener('dragenter', function(e) {
            if (e.dataTransfer.types.includes('Files')) {
                dragOverlay.classList.add('active');
            }
        });
        
        document.addEventListener('dragleave', function(e) {
            // Only hide if leaving the document (not entering a child element)
            if (e.currentTarget.contains(e.relatedTarget) === false) {
                dragOverlay.classList.remove('active');
            }
        });
        
        document.addEventListener('dragover', function(e) {
            // Prevent default to allow drop
            e.preventDefault();
        });
        
        document.addEventListener('drop', function(e) {
            // Hide overlay when dropping anywhere
            dragOverlay.classList.remove('active');
            
            // Prevent default browser behavior
            e.preventDefault();
        });
    }

    // Обработчик клика для изображений и видео
    document.querySelectorAll('.media-thumbnail').forEach(thumb => {
        thumb.addEventListener('click', function() {
            const type = this.dataset.mediaType;
            const src = this.dataset.mediaSrc;
            
            // Находим все медиа файлы в текущем посте
            const postGallery = this.closest('.post-media-gallery');
            if (postGallery) {
                currentPostMedia = Array.from(postGallery.querySelectorAll('.media-thumbnail')).map(thumb => ({
                    type: thumb.dataset.mediaType,
                    src: thumb.dataset.mediaSrc
                }));
                
                // Находим индекс текущего медиа файла
                currentMediaIndex = currentPostMedia.findIndex(media => media.src === src);
            } else {
                // If not in a gallery, treat as single item
                currentPostMedia = [{ type: type, src: src }];
                currentMediaIndex = 0;
            }
            
            showMediaInModal(type, src);
            // updateNavigationButtons moved to showMediaInModal after media loads
        });
    });

    // Функция для показа медиа в модальном окне
    function showMediaInModal(type, src) {
        // Clear previous content
        mediaContent.innerHTML = `
            <div class="spinner-border text-primary" role="status">
                <span class="visually-hidden">Загрузка...</span>
            </div>
        `;
        
        // Always hide navigation buttons initially
        prevMediaBtn.classList.add('d-none');
        nextMediaBtn.classList.add('d-none');
        
        const downloadBtn = document.getElementById('downloadMediaBtn');
        const mediaFileName = document.getElementById('mediaFileName');
        const mediaFileSize = document.getElementById('mediaFileSize');
        
        // Set download link
        downloadBtn.href = src;
        
        // Extract filename from path
        const filename = src.split('/').pop();
        downloadBtn.setAttribute('download', filename);
        mediaFileName.textContent = filename;
        
        // Create media element
        const mediaElement = type === 'image' ? document.createElement('img') : document.createElement('video');
        mediaElement.className = 'w-100';
        
        // Adjust styling for responsive display
        mediaElement.style.maxHeight = window.innerWidth < 768 ? '60vh' : '80vh';
        mediaElement.style.objectFit = 'contain';
        
        if (type === 'image') {
            mediaElement.alt = 'Просмотр изображения';
            mediaElement.src = src;
            document.getElementById('mediaModalLabel').textContent = 'Просмотр изображения';
        } else {
            mediaElement.controls = true;
            mediaElement.autoplay = true;
            
            const source = document.createElement('source');
            source.src = src;
            source.type = 'video/mp4';
            mediaElement.appendChild(source);
            
            document.getElementById('mediaModalLabel').textContent = 'Просмотр видео';
        }
        
        // Load media and show size
        if (type === 'image') {
            const img = new Image();
            img.onload = function() {
                mediaContent.innerHTML = '';
                mediaContent.appendChild(mediaElement);
                mediaFileSize.textContent = formatFileSize(this.naturalWidth * this.naturalHeight * 4); // Approximate size
                
                // Important: Call this after content is added and visible
                setTimeout(updateNavigationButtons, 0);
            };
            img.src = src;
        } else {
            mediaElement.onloadedmetadata = function() {
                mediaContent.innerHTML = '';
                mediaContent.appendChild(mediaElement);
                mediaFileSize.textContent = formatFileSize(this.duration * 1024 * 1024); // Approximate size
                
                // Important: Call this after content is added and visible
                setTimeout(updateNavigationButtons, 0);
            };
            mediaElement.src = src;
        }
        
        // Show modal and ensure responsiveness
        mediaModal.show();
        
        // Add a resize event listener to adjust for window size changes
        const handleResize = () => {
            if (mediaContent.firstElementChild && mediaContent.firstElementChild.tagName !== 'DIV') {
                mediaContent.firstElementChild.style.maxHeight = window.innerWidth < 768 ? '60vh' : '80vh';
            }
            updateNavigationButtons();
        };
        
        // Remove any existing resize listener
        window.removeEventListener('resize', handleResize);
        
        // Add resize listener
        window.addEventListener('resize', handleResize);
        
        // Ensure that navigation buttons are correctly positioned
        setTimeout(() => {
            // Force buttons to be repositioned
            const modalBody = document.querySelector('#mediaModal .modal-body');
            if (modalBody) {
                // Ensure buttons are visible if there are multiple media items
                if (currentPostMedia.length > 1) {
                    console.log('Multiple media items detected:', currentPostMedia.length);
                    updateNavigationButtons();
                }
            }
        }, 300);
    }

    // Функция для обновления состояния кнопок навигации
    function updateNavigationButtons() {
        console.log('Updating navigation buttons. Current index:', currentMediaIndex, 'Total items:', currentPostMedia.length);
        
        // Always hide both buttons first
        prevMediaBtn.classList.add('d-none');
        nextMediaBtn.classList.add('d-none');
        
        // If there's only one or no media items, keep buttons hidden
        if (currentPostMedia.length <= 1) {
            console.log('Only one or no media items, hiding buttons');
            return;
        }
        
        console.log('Multiple media items detected:', currentPostMedia.length);
        
        // Show prev button if not on first item
        if (currentMediaIndex > 0) {
            prevMediaBtn.classList.remove('d-none');
            console.log('Showing prev button');
        }
        
        // Show next button if not on last item
        if (currentMediaIndex < currentPostMedia.length - 1) {
            nextMediaBtn.classList.remove('d-none');
            console.log('Showing next button');
        }
        
        // Force buttons to be visible by setting style directly
        if (currentMediaIndex > 0) {
            prevMediaBtn.style.display = 'flex';
        }
        
        if (currentMediaIndex < currentPostMedia.length - 1) {
            nextMediaBtn.style.display = 'flex';
        }
    }

    // Обработчики для кнопок навигации
    prevMediaBtn.addEventListener('click', function() {
        console.log('Previous button clicked, current index:', currentMediaIndex);
        if (currentMediaIndex > 0) {
            currentMediaIndex--;
            const media = currentPostMedia[currentMediaIndex];
            showMediaInModal(media.type, media.src);
            // Remove the updateNavigationButtons call here since it's already called in showMediaInModal
        }
    });

    nextMediaBtn.addEventListener('click', function() {
        console.log('Next button clicked, current index:', currentMediaIndex);
        if (currentMediaIndex < currentPostMedia.length - 1) {
            currentMediaIndex++;
            const media = currentPostMedia[currentMediaIndex];
            showMediaInModal(media.type, media.src);
            // Remove the updateNavigationButtons call here since it's already called in showMediaInModal
        }
    });

    // Закрытие модального окна очищает его содержимое и останавливает видео
    document.getElementById('mediaModal').addEventListener('hidden.bs.modal', function() {
        const video = mediaContent.querySelector('video');
        if (video) {
            video.pause();
            video.currentTime = 0;
        }
        mediaContent.innerHTML = '';
        document.getElementById('mediaFileName').textContent = '';
        document.getElementById('mediaFileSize').textContent = '';
        currentPostMedia = [];
        currentMediaIndex = 0;
    });

    // Добавляем обработчик клавиши Escape для закрытия модального окна
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape' && document.getElementById('mediaModal').classList.contains('show')) {
            const modal = bootstrap.Modal.getInstance(document.getElementById('mediaModal'));
            if (modal) {
                modal.hide();
            }
        } else if (e.key === 'ArrowLeft' && document.getElementById('mediaModal').classList.contains('show')) {
            prevMediaBtn.click();
        } else if (e.key === 'ArrowRight' && document.getElementById('mediaModal').classList.contains('show')) {
            nextMediaBtn.click();
        }
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
        const fileCountElement = document.getElementById('file-count');
        const dropZone = document.getElementById('drop-zone');
        const MAX_FILES = 5;

        // Setup global drag-and-drop indicator
        const body = document.body;
        let dragCounter = 0;
        
        // Create page overlay for drag feedback
        const overlay = document.createElement('div');
        overlay.className = 'drag-overlay';
        overlay.innerHTML = `
            <div class="drag-overlay-content">
                <i class="fas fa-cloud-upload-alt fa-4x mb-3"></i>
                <h3>Перетащите файлы сюда</h3>
                <p>Отпустите файлы, чтобы загрузить их</p>
            </div>
        `;
        body.appendChild(overlay);

        // Track file dragging over the document
        document.addEventListener('dragenter', function(e) {
            dragCounter++;
            if (e.dataTransfer.types.includes('Files')) {
                overlay.classList.add('active');
            }
        });
        
        document.addEventListener('dragleave', function(e) {
            dragCounter--;
            if (dragCounter === 0) {
                overlay.classList.remove('active');
            }
        });
        
        document.addEventListener('drop', function() {
            dragCounter = 0;
            overlay.classList.remove('active');
        });

        // Setup drag and drop functionality
        if (dropZone) {
            // Prevent default behaviors for these events
            ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, preventDefaults, false);
                document.body.addEventListener(eventName, preventDefaults, false);
            });
            
            // Add highlight effect when dragging over drop zone
            ['dragenter', 'dragover'].forEach(eventName => {
                dropZone.addEventListener(eventName, highlight, false);
            });
            
            // Remove highlight effect when dragging leaves drop zone
            ['dragleave', 'drop'].forEach(eventName => {
                dropZone.addEventListener(eventName, unhighlight, false);
            });
            
            // Handle file drop
            dropZone.addEventListener('drop', handleDrop, false);
            
            // Open file dialog when clicking on drop zone
            dropZone.addEventListener('click', function(e) {
                // Only open file dialog when clicking directly on the drop zone
                // or the browse text, not when clicking on thumbnails
                if (e.target.closest('.preview-item') === null) {
                    mediaInput.click();
                }
            });
            
            // Specific handler for the browse text
            const browseButton = dropZone.querySelector('.drop-zone-browse');
            if (browseButton) {
                browseButton.addEventListener('click', function(e) {
                    e.stopPropagation();  // Prevent dropzone click event
                    mediaInput.click();
                });
            }

            // Helper functions for drag and drop
            function preventDefaults(e) {
                e.preventDefault();
                e.stopPropagation();
            }
            
            function highlight() {
                dropZone.classList.add('drop-zone-drag');
            }
            
            function unhighlight() {
                dropZone.classList.remove('drop-zone-drag');
            }
            
            function handleDrop(e) {
                const dt = e.dataTransfer;
                const files = dt.files;
                
                if (files.length > MAX_FILES) {
                    alert(`Вы можете загрузить максимум ${MAX_FILES} файлов одновременно.`);
                    return;
                }
                
                mediaInput.files = files; // Set the files to the input
                const event = new Event('change'); // Create a change event
                mediaInput.dispatchEvent(event); // Dispatch the event to trigger the file handling
            }
        }

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

        // Media files preview
        mediaInput.addEventListener('change', function() {
            const files = this.files;
            
            // Enforce max file limit
            if (files.length > MAX_FILES) {
                alert(`Вы можете загрузить максимум ${MAX_FILES} файлов одновременно.`);
                this.value = ''; // Clear the selection
                return;
            }
            
            // Update file count
            fileCountElement.textContent = `Выбрано файлов: ${files.length}/${MAX_FILES}`;
            
            if (files.length > 0) {
                // Show preview container and clear previous previews
                mediaPreviewContainer.classList.remove('d-none');
                mediaPreview.innerHTML = '';
                
                // Create a preview for each file
                Array.from(files).forEach((file, index) => {
                    createFilePreview(file, index);
                });
                
                // Hide prompt if files are selected
                if (dropZone.querySelector('.drop-zone-prompt')) {
                    dropZone.querySelector('.drop-zone-prompt').style.display = 'none';
                }
            } else {
                // Hide preview if no files selected
                mediaPreviewContainer.classList.add('d-none');
                
                // Show prompt if no files
                if (dropZone.querySelector('.drop-zone-prompt')) {
                    dropZone.querySelector('.drop-zone-prompt').style.display = 'block';
                }
            }
        });

        // Create preview for a file
        function createFilePreview(file, index) {
            const fileType = file.type;
            const reader = new FileReader();
            const previewItem = document.createElement('div');
            previewItem.className = 'preview-item position-relative';
            previewItem.dataset.index = index;
            
            // Add loading indicator
            previewItem.innerHTML = `
                <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">Загрузка...</span>
                </div>
            `;
            
            mediaPreview.appendChild(previewItem);
            
            reader.onload = function(e) {
                if (fileType.startsWith('image/')) {
                    // Image preview
                    previewItem.innerHTML = `
                        <div class="position-relative" style="width: 120px; height: 120px;">
                            <img src="${e.target.result}" class="img-thumbnail" style="width: 120px; height: 120px; object-fit: cover;" alt="Предпросмотр ${index + 1}">
                            <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 remove-file" data-index="${index}">
                                <i class="fas fa-times"></i>
                            </button>
                            <div class="position-absolute bottom-0 start-0 end-0 bg-dark bg-opacity-75 text-white p-1 small text-truncate">
                                ${file.name.split('.')[0]}
                            </div>
                            <span class="badge bg-success position-absolute top-0 start-0 m-1" title="Размер файла">
                                ${formatFileSize(file.size)}
                            </span>
                        </div>
                    `;
                } else if (fileType.startsWith('video/')) {
                    // Video preview
                    previewItem.innerHTML = `
                        <div class="position-relative" style="width: 120px; height: 120px;">
                            <div class="bg-dark d-flex align-items-center justify-content-center" style="width: 120px; height: 120px;">
                                <i class="fas fa-film fa-3x text-light"></i>
                            </div>
                            <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 remove-file" data-index="${index}">
                                <i class="fas fa-times"></i>
                            </button>
                            <div class="position-absolute bottom-0 start-0 end-0 bg-dark bg-opacity-75 text-white p-1 small text-truncate">
                                ${file.name.split('.')[0]}
                            </div>
                            <span class="badge bg-primary position-absolute top-0 start-0 m-1">Видео</span>
                            <span class="badge bg-success position-absolute top-0 start-0 mt-4 m-1" title="Размер файла">
                                ${formatFileSize(file.size)}
                            </span>
                        </div>
                    `;
                } else {
                    // Unsupported file type
                    previewItem.innerHTML = `
                        <div class="position-relative" style="width: 120px; height: 120px;">
                            <div class="bg-light d-flex flex-column align-items-center justify-content-center" style="width: 120px; height: 120px;">
                                <i class="fas fa-file fa-3x text-secondary mb-2"></i>
                                <span class="small text-truncate px-1">${file.name.split('.')[0]}</span>
                            </div>
                            <button type="button" class="btn btn-sm btn-danger position-absolute top-0 end-0 remove-file" data-index="${index}">
                                <i class="fas fa-times"></i>
                            </button>
                            <span class="badge bg-secondary position-absolute bottom-0 start-0 m-1" title="Размер файла">
                                ${formatFileSize(file.size)}
                            </span>
                        </div>
                    `;
                }
                
                // Add event listener to individual remove buttons
                const removeBtn = previewItem.querySelector('.remove-file');
                if (removeBtn) {
                    removeBtn.addEventListener('click', function(e) {
                        e.preventDefault();
                        e.stopPropagation(); // Prevent triggering the dropzone click
                        removeFile(parseInt(this.dataset.index));
                    });
                }
            };
            
            reader.readAsDataURL(file);
        }
        
        // Function to remove a specific file
        function removeFile(index) {
            const dt = new DataTransfer();
            const files = mediaInput.files;
            
            // Add all files except the one to remove
            for (let i = 0; i < files.length; i++) {
                if (i !== index) {
                    dt.items.add(files[i]);
                }
            }
            
            // Update the file input with the new list
            mediaInput.files = dt.files;
            
            // Trigger change event to update preview
            const event = new Event('change');
            mediaInput.dispatchEvent(event);
        }

        // Remove all media files button
        removeMediaBtn.addEventListener('click', function() {
            mediaInput.value = '';
            mediaPreviewContainer.classList.add('d-none');
            mediaPreview.innerHTML = '';
            fileCountElement.textContent = `Выбрано файлов: 0/${MAX_FILES}`;
            
            // Show prompt again
            if (dropZone.querySelector('.drop-zone-prompt')) {
                dropZone.querySelector('.drop-zone-prompt').style.display = 'block';
            }
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
            const fileInputs = this.querySelectorAll('input[type="file"]');
            let totalSize = 0;
            let filesExceedLimit = false;
            
            fileInputs.forEach(fileInput => {
                if (fileInput && fileInput.files.length > 0) {
                    // Check each file
                    Array.from(fileInput.files).forEach(file => {
                        totalSize += file.size;
                        
                        // Конвертируем предел 100 МБ в байты
                        const maxSize = 100 * 1024 * 1024;
                        
                        if (file.size > maxSize) {
                            filesExceedLimit = true;
                        }
                    });
                }
            });
            
            if (filesExceedLimit) {
                e.preventDefault();
                alert('Один или несколько файлов превышают допустимый лимит в 100 МБ.');
            }
        });
    });
    
    // Initialize thumbnails in existing posts
    document.querySelectorAll('.post-media-gallery').forEach(gallery => {
        gallery.querySelectorAll('.media-thumbnail').forEach(thumb => {
            thumb.addEventListener('click', function() {
                const type = this.dataset.mediaType;
                const src = this.dataset.mediaSrc;
                showMediaInModal(type, src);
            });
        });
    });
});