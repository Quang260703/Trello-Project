// JavaScript to toggle the dropdown menu
function onMenuClick() {
    document.getElementById('menuToggle').addEventListener('click', function() {
        document.getElementById("myDropdown").classList.toggle("show");
    });
};

// Close the dropdown if the user clicks outside of it
window.onclick = function(e) {
    if (!e.target.matches('#menuToggle') && !e.target.matches('.nav__link')) {
        var myDropdown = document.getElementById("myDropdown");
        if (myDropdown.classList.contains('show')) {
            myDropdown.classList.remove('show');
        };
    };
};