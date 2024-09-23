document.addEventListener("DOMContentLoaded", function() {
    if (window.innerWidth < 767) {
        return;
    }

    var banner = document.createElement("div");
    banner.className = 'donation-banner';
    banner.innerHTML = '<img src="https://raw.githubusercontent.com/globaleaks/whistleblowing-software/main/brand/assets/heart.svg" class="donation-icon" alt="Donate" /> Globaleaks is free and open-source whistleblowing software. <a href="https://github.com/sponsors/globaleaks">Donate here to support its development!</a>';
    document.body.insertBefore(banner, document.body.firstChild);
});
