// Javascript to handle login
jQuery(document).ready(function() {       
    let count = 0
    let action = '';

    jQuery('#searchForm button').on('click', function () {
        action = jQuery(this).attr('name'); // Store the button's 'name' attribute
    });

    // Attach a submit handler to the form
    jQuery('#searchForm').on('submit', function(event) {
        // Stop form from submitting normally
        event.preventDefault();

        // Get email and password input values
        const email = jQuery('input[name="email"]').val();
        const password = jQuery('input[name="password"]').val();

        // Package data in a JSON object
        const login_data = { 'email': email, 'password': password };

        const endpoint = action === 'login' ? "/processlogin" : "/processsignup";

        // SEND DATA TO SERVER VIA jQuery.ajax({})
        jQuery.ajax({
            url: endpoint,
            data: login_data,
            type: "POST",
            dataType: "json",  // Ensure the response is treated as JSON
            success:function(returned_data){
                if (returned_data.success) {
                    window.location.href = "/home";
                }
                else {
                    count+=1;
                    jQuery('.login__error').text(returned_data['fail'] + ": " + count);
                    jQuery('.login__error').show();
                }
            },
            error:function(xhr, status, error){
                count+=1;
                jQuery('.login__error').text(returned_data['fail'] + ": " + count);
                jQuery('.login__error').show();
            }
        })
    })
})
