document.addEventListener("DOMContentLoaded", function () {
    const fileInput = document.getElementById("data-file");
    const selectedFileName = document.getElementById("selected-file-name");

    if (!fileInput || !selectedFileName) {
        return;
    }

    fileInput.addEventListener("change", function () {
        if (fileInput.files.length > 0) {
            selectedFileName.textContent = fileInput.files[0].name;
        } else {
            selectedFileName.textContent = "Файл не выбран";
        }
    });
});