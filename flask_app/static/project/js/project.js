$(document).ready(function() {
    let socket = io.connect('https://' + document.domain + ':' + location.port + '/board');

    $(document).on('click', '.project__delete', function() {
        var card = $(this).closest('.project__card');
        var cardId = card.attr('id');  // Get the card_id from the element's ID attribute
        // Emit delete_card event to the server via socket
        socket.emit('delete_card', { 'card_id': cardId });
    });

    // Listen for the 'card_deleted' event from the server
    socket.on('card_deleted', function(data) {
        var cardId = data.card_id;
        var card = $('#' + cardId);  // Assuming the card's ID is the same as the card element's ID
        card.remove();  // Remove the card from the DOM
    });

    // Listen for errors
    socket.on('error', function(data) {
        alert(data.msg);  // Display error message
    });

    $(document).on('click', '.project__edit', function() {
        var card = $(this).closest('.project__card');
        var cardId = card.attr('id');  // Get the card_id from the element's ID attribute
        var button = $(this);  // Capture the button reference
        var columnId = card.closest('.project__column').attr('id');

        // Check if the card is already being edited
        if (button.text() === 'Save') {
            // Save changes here (add your save logic)
            var input = card.find('input');
            var textarea = card.find('textarea');

            // Check if the fields are empty
            if (input.val() === "") {
                alert("Card name cannot be empty");
                return; // Stop the save operation if fields are empty
            }

            socket.emit('edit_card', { 'card_id': cardId, 'name': input.val(), 'description': textarea.val() });
            socket.emit('unlocked_column', {'column_id': columnId});
        } 
        else {
            // Enable the input and textarea fields for editing
            card.find('input, textarea').prop('disabled', false);   
            // Change the button text to "Save"
            button.text('Save');
            socket.emit('locked_column', {'column_id': columnId});
        }
    });

    socket.on('column_locked', function(data) {
        var column = $('#' + data.column_id);
    
        // Apply pointer-events: none to lock the column for other users
        column.css('pointer-events', 'none');
    });

    socket.on('column_unlocked', function(data) {
        var column = $('#' + data.column_id);
    
        // Apply pointer-events: none to lock the column for other users
        column.css('pointer-events', 'auto');
    });

    // Handle "Enter" key press to emit the 'edit_card' event
    $(document).on('keydown', '.project__card input, .project__card textarea', function(e) {
        if (e.key === 'Enter') {
            var card = $(this).closest('.project__card');  // Find the closest parent card
            var button = card.find('.project__edit');  // Find the Edit button
            var columnId = card.closest('.project__column').attr('id');

            // Only allow the save if the card is in edit mode (i.e., button text is "Save")
            if (button.text() === 'Save') {
                var cardId = card.attr('id');
                var input = card.find('input');
                var textarea = card.find('textarea');

                // Ensure input and textarea have values and aren't empty
                if (input.val() === "") {
                    alert("Card name cannot be empty");
                    return; // Stop if name field is empty
                }

                // Emit the event to save the card
                socket.emit('edit_card', {
                    'card_id': cardId,
                    'name': input.val(),
                    'description': textarea.val()
                });

                socket.emit('unlocked_column', {'column_id': columnId});
            }
        }
    });

    // Listen for the 'card_updated' event to update the card content for all clients
    socket.on('card_edited', function(data) {
        var card = $('#' + data.card_id); // Find the card by its ID
        card.find('input').val(data.name).prop('disabled', true); // Update name and disable input
        card.find('textarea').val(data.description).prop('disabled', true); // Update description and disable textarea
        card.find('.project__edit').text('Edit'); // Change button back to 'Edit'
    });

    $(document).on('click', '.project__add', function() {
        var elementId = $(this).attr('id');
        let parentId = 0;
        if (elementId === 'addTodo') {
            parentId = 0 // Adjust the selector to match the parent element
        }
        else if (elementId === 'addDoing') {
            parentId = 1 // Adjust the selector to match the parent element
        }
        else {
            parentId = 2
        }
        // Emit event to create the card on the server
        socket.emit('create_card', {
            list_id: parentId,
            name: 'New Card',
            description: 'New description'
        });
    })

    socket.on('card_created', function(data) {
        const newCard = document.createElement('div');
        newCard.className = 'project__card';
        newCard.id = data.card_id;
        newCard.draggable = "true";

        // Create and append input
        const input = document.createElement('input');
        input.className = 'project__input';
        input.value = 'New Card';
        input.disabled = true;
        newCard.appendChild(input);

        // Create and append edit button
        const editButton = document.createElement('button');
        editButton.type = 'button';
        editButton.name = 'edit';
        editButton.id = 'editButton'
        editButton.className = 'project__edit';
        editButton.textContent = 'Edit';
        newCard.appendChild(editButton);

        // Create and append textarea
        const textarea = document.createElement('textarea');
        textarea.className = 'project__input';
        textarea.textContent = 'New description';
        textarea.disabled = true;
        newCard.appendChild(textarea);

        // Create and append delete button
        const deleteButton = document.createElement('button');
        deleteButton.type = 'button';
        deleteButton.name = 'del';
        deleteButton.className = 'project__delete';
        deleteButton.id = 'delButton'
        newCard.appendChild(deleteButton);

        $('.project__column').each(function() {
            if ($(this).attr('id') == data.list_id) {
                $(this).append(newCard);  // Append newCard to the matching parent
            }
        })

        // Reapply the drag and drop functionality to the newly created card
        newCard.addEventListener('dragstart', () => {
            newCard.classList.add('dragging');
        });

        newCard.addEventListener('dragend', () => {
            newCard.classList.remove('dragging');
        });
    })

    const cards = document.querySelectorAll('.project__card')
    const droppable = document.querySelectorAll('.project__column')
    cards.forEach(card => {
        card.addEventListener('dragstart', () => {
            card.classList.add('dragging')
        })

        card.addEventListener('dragend', () => {
            card.classList.remove('dragging')
        })
    })

    droppable.forEach((droppable, idx) => {
        droppable.addEventListener('dragover', e => {
            e.preventDefault()
            const position = getInsertedPosition(droppable, e.clientY)
            const card = document.querySelector('.dragging')
            if (position == null) {
                droppable.appendChild(card)
            }
            else {
                droppable.insertBefore(card, position)
            } 
        })

        droppable.addEventListener('drop', e => {
            e.preventDefault();  // Prevent default behavior (e.g., opening as link)
    
            const card = document.querySelector('.dragging')
            const cardIndex = getCardIndex(droppable, card);

            console.log(card.getAttribute('id'), idx, cardIndex)
            socket.emit('move_card', { 
                card_id: card.getAttribute('id'), 
                list_id: idx, 
                position: cardIndex,
            });
        })
    })

    function getInsertedPosition(droppable, y) {
        const cardElements = [...droppable.querySelectorAll('.project__card:not(.dragging)')]

        return cardElements.reduce((closest, child) => {
            const box = child.getBoundingClientRect()
            const offset = y - box.top - box.height / 2
            if (offset < 0 && offset > closest.offset) {
                return { offset: offset, element: child }; // Element is above the mouse pointer
            } 
            else {
                return closest;
            }
        }, { offset: Number.NEGATIVE_INFINITY }).element || null
    }

    function getCardIndex(droppable, card) {
        const cards = [...droppable.querySelectorAll('.project__card')];
        return cards.indexOf(card);  // Returns the index of the dragged card within the column
    }

    socket.on('move_card', function(data) {
        const { list_id, card_id, position } = data;
        
        // Find the column by ID and the card by its ID
        const column = document.querySelector(`#\\3${list_id}.project__column`);
        const card = document.querySelector(`#\\3${card_id}.project__card`);

        const cards = [...column.querySelectorAll('.project__card')];  // Get all cards in the droppable
        insert_card = cards[position] || null;
        console.log(insert_card)  

        // Insert the card into the correct position
        if (insert_card == null) {
            column.appendChild(card);
        } else {
            column.insertBefore(card, insert_card)  // If no target card, append it at the end
        }
    });

    const currentUser = document.getElementById('currentUser').value;

    socket.on('connect', function() {
        socket.emit('joined', { 'user': currentUser });
    });

    // Listen for the "Enter" key press on the message input
    $('input[name="message"]').on('keypress', function(event) {
        // Check if the "Enter" key (key code 13) is pressed
        if (event.which === 13) {
            // Prevent the default action (form submission if inside a form)
            event.preventDefault();

            // Get the message from the input field
            var message = $(this).val();

            // Emit the message to the server
            socket.emit('send_message', {  'user': currentUser, 'msg': message });

            // Clear the input field after sending the message
            $(this).val('');
        }
    });

    socket.on('status', function(data) {     
        const currentUser = document.getElementById('currentUser').value;
        let tag = document.createElement("p");
        let text = document.createTextNode(data.msg);
        tag.appendChild(text);

        // Style based on whether the message is from the current user
        if (data.user === currentUser) {
            tag.style.cssText = 'width: 100%; color: blue; text-align: right;';
        } else {
            tag.style.cssText = 'width: 100%; color: grey; text-align: left;';
        }

        const element = document.getElementById("project__chat");
        element.appendChild(tag);

        $('.project__chat').scrollTop($('.project__chat')[0].scrollHeight);
    });
});