document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("data-file");
    const selectedFileName = document.getElementById("selected-file-name");
    const uploadBox = document.querySelector(".upload-box");

    if (!fileInput || !selectedFileName) {
        return;
    }

    // Обработка выбора файла через input
    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            selectedFileName.textContent = fileInput.files[0].name;
        } else {
            selectedFileName.textContent = "Файл не выбран";
        }
    });

    // Drag and drop функциональность
    if (uploadBox) {
        // Предотвращение стандартного поведения браузера при drag over
        ["dragenter", "dragover", "dragleave", "drop"].forEach(eventName => {
            uploadBox.addEventListener(eventName, preventDefaults, false);
            document.body.addEventListener(eventName, preventDefaults, false);
        });

        function preventDefaults(e) {
            e.preventDefault();
            e.stopPropagation();
        }

        // Визуальная обратная связь при drag over
        ["dragenter", "dragover"].forEach(eventName => {
            uploadBox.addEventListener(eventName, highlightBox, false);
        });

        ["dragleave", "drop"].forEach(eventName => {
            uploadBox.addEventListener(eventName, unhighlightBox, false);
        });

        function highlightBox(e) {
            uploadBox.classList.add("highlight");
        }

        function unhighlightBox(e) {
            uploadBox.classList.remove("highlight");
        }

        // Обработка drop события
        uploadBox.addEventListener("drop", handleDrop, false);

        function handleDrop(e) {
            const dt = e.dataTransfer;
            const files = dt.files;

            if (files.length > 0) {
                // Устанавливаем файл в input
                fileInput.files = files;

                // Триггер события change для обновления имени файла
                const event = new Event("change", { bubbles: true });
                fileInput.dispatchEvent(event);

                // Автоматически отправляем форму
                const form = fileInput.closest("form");
                if (form) {
                    form.submit();
                }
            }
        }
    }
});