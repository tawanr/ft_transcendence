import * as constants from "./constants.js";
import { getUserToken } from "./utils.js";

imgInput.onchange = (e) => {
    const [file] = imgInput.files;
    const imagePreview = document.getElementById("imagePreview");
    if (file) {
        imagePreview.src = URL.createObjectURL(file);
        imagePreview.classList.remove("d-none");
    }
};

function submitImage(e) {
    e.preventDefault();
    const [file] = imgInput.files;
    const apiUrl = constants.BACKEND_HOST + "/account/avatar/";
    if (file) {
        const formData = new FormData();
        formData.append("image", file);
        const token = getUserToken();
        fetch(apiUrl, {
            method: "POST",
            body: formData,
            headers: {
                Authorization: "Bearer " + token,
            },
        })
            .then((response) => response.json())
            .then((data) => {
                if (data.success) {
                    window.location.reload();
                } else {
                    alert("Error uploading image");
                }
            });
    }
}

document.getElementById("uploadBtn").addEventListener("click", submitImage);
