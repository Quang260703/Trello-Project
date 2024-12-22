jQuery(document).ready(function() {   
    const addEmailBtn = document.getElementById('addButton');
    const emailInput = document.getElementById('emailInput');
    const emailDisplayContainer = document.getElementById('memberEmailContainer');

    let emailList = []

    addEmailBtn.addEventListener('click', () => {
        const emailValue = emailInput.value.trim();  // Get the email value
        if (emailList.includes(emailValue)) {
            jQuery('.create__error').text("This email has already been added");
            jQuery('.create__error').show();
        }
        else {
            const email_data = { 'email': emailValue };

            // SEND DATA TO SERVER VIA jQuery.ajax({})
            jQuery.ajax({
                url: '/validateemail',
                data: email_data,
                type: "GET",
                dataType: "json",  // Ensure the response is treated as JSON
                success:function(returned_data){
                    if (returned_data.success) {
                                // Create a new div to display the email
                        const emailDisplayDiv = document.createElement('div');
                        emailDisplayDiv.classList.add('create__container');

                        const emailText = document.createElement('span');
                        emailText.textContent = emailValue;
                        emailText.classList.add('create__input');

                        const removeButton = document.createElement('button');
                        removeButton.type = 'button';
                        removeButton.classList.add('create__delete');

                        // Append email and remove button to the div
                        emailDisplayDiv.appendChild(emailText);
                        emailDisplayDiv.appendChild(removeButton);

                        // Add the new email to the container
                        emailDisplayContainer.appendChild(emailDisplayDiv);

                        // Clear the input field after adding the email
                        emailInput.value = '';

                        // Remove the email from the display when the remove button is clicked
                        removeButton.addEventListener('click', () => {
                            emailList = emailList.filter(element => element !== emailText.textContent);
                            emailDisplayContainer.removeChild(emailDisplayDiv);
                        });

                        emailList.push(emailValue)
                        jQuery('.create__error').hide();
                    }
                    else {
                        jQuery('.create__error').text(returned_data['fail']);
                        jQuery('.create__error').show();
                    }
                },
                error:function(xhr, status, error){
                    jQuery('.create__error').text(returned_data['fail']);
                    jQuery('.create__error').show();
                }
            })
        }
    });

    jQuery('#createForm').on('submit', function(event) {
        // Stop form from submitting normally
        event.preventDefault();

        if (emailList.length === 0) {
            jQuery('.create__error').text("Please add board member email");
            jQuery('.create__error').show();
        }
        else {
            const name = jQuery('input[name="name"]').val();
            const create_data = JSON.stringify({ 'name': name, 'email': emailList });
            console.log(create_data)
            // SEND DATA TO SERVER VIA jQuery.ajax({})
            jQuery.ajax({
                url: '/processcreate',
                data: create_data,
                type: "POST",
                dataType: "json",  // Ensure the response is treated as JSON
                success:function(returned_data){
                    if (returned_data.success) {
                        window.location.href = "/board/" + returned_data['success'];
                    }
                    else {
                        jQuery('.create__error').text(returned_data['fail']);
                        jQuery('.create__error').show();
                    }
                },
                error:function(xhr, status, error){
                    jQuery('.create__error').text(returned_data['fail']);
                    jQuery('.create__error').show();
                }
            })
        }
    })
})