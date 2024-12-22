// JavaScript to redirect to pages
jQuery(document).ready(function() {
    jQuery('#open').on('click', function() {
        window.location.href = '/board';
    });
    jQuery('#create').on('click', function() {
        window.location.href = '/create';
    });
});