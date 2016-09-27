(function() {
    var text = document.getElementById("synopsis");
    var counter = document.getElementById("synopsis-char-counter");
    var savebtn = document.getElementById("recipe-save-btn");

    function updateCharCount() {
        var ctr = text.value.length;
        if(ctr > 140) {
            ctr = "<span style='color:red'>" + ctr + "</span>";
            savebtn.setAttribute("disabled", true);
        }
        else {
            savebtn.removeAttribute("disabled");
        }
        counter.innerHTML = ctr + "/140";
    };

    text.addEventListener("keyup", updateCharCount);
    text.addEventListener("click", updateCharCount);
    text.addEventListener("change", updateCharCount);
    text.addEventListener("focus", updateCharCount);
    text.addEventListener("blur", updateCharCount);

    updateCharCount();
})();
