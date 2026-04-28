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

    // Фильтрация таблицы предпросмотра по дисциплине
    const filterSelect = document.getElementById("preview-discipline-filter");
    const previewTable = document.getElementById("preview-table");
    const filterInfo = document.getElementById("preview-filter-info");

    if (filterSelect && previewTable) {
        filterSelect.addEventListener("change", function () {
            const selectedDiscipline = this.value;

            // Отправляем AJAX запрос на сервер для получения отфильтрованных данных
            fetch("/api/preview-filter", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify({
                    discipline: selectedDiscipline
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Очищаем текущие строки таблицы
                    const tbody = previewTable.querySelector("tbody");
                    tbody.innerHTML = "";

                    // Добавляем новые строки
                    data.rows.forEach(row => {
                        const tr = document.createElement("tr");
                        tr.setAttribute("data-discipline", row["Дисциплина"]);
                        tr.innerHTML = `
                            <td>${row["ФИО студента"]}</td>
                            <td>${row["Группа"]}</td>
                            <td>${row["Дисциплина"]}</td>
                            <td>${row["Метод обучения"]}</td>
                            <td>${row["Оценка / балл за тест"]}</td>
                        `;
                        tbody.appendChild(tr);
                    });

                    // Обновляем информацию о количестве видимых строк
                    if (selectedDiscipline === "") {
                        filterInfo.textContent = `Всего строк: ${data.total}`;
                    } else {
                        filterInfo.textContent = `Показано: ${data.rows.length} из ${data.total}`;
                    }
                } else {
                    console.error("Ошибка:", data.error);
                    filterInfo.textContent = "Ошибка при фильтрации";
                }
            })
            .catch(error => {
                console.error("Ошибка при запросе:", error);
                filterInfo.textContent = "Ошибка при фильтрации";
            });
        });

        // Установка начального значения информации
        const totalRows = previewTable.querySelectorAll("tbody tr").length;
        if (filterInfo) {
            filterInfo.textContent = `Всего строк: ${totalRows}`;
        }
    }
});