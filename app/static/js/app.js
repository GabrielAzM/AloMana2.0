(function () {
    var storageKey = "alomana-theme";
    var body = document.body;
    var toggle = document.getElementById("dark-mode-toggle");

    function applyTheme(theme) {
        if (theme === "dark") {
            body.classList.add("dark-theme");
            if (toggle) {
                toggle.checked = true;
            }
        } else {
            body.classList.remove("dark-theme");
            if (toggle) {
                toggle.checked = false;
            }
        }
    }

    var savedTheme = localStorage.getItem(storageKey);
    applyTheme(savedTheme === "dark" ? "dark" : "light");

    if (toggle) {
        toggle.addEventListener("change", function () {
            var nextTheme = toggle.checked ? "dark" : "light";
            localStorage.setItem(storageKey, nextTheme);
            applyTheme(nextTheme);
        });
    }
})();
