jQuery(document).ready(function() {
    jQuery('.main__column').on('click', function() {
        const id = this.id;  // Get the id directly from the element
        window.location.href = `/board/${id}`;  // Redirect to the dynamic URL
    });
});