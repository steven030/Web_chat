const socket = io();
const currentUsername = window.currentUser || "";
let currentReceiverId = null;

socket.on('connect', () => {
    socket.emit('join_private');
});

function selectUser(userId, username) {
    currentReceiverId = userId;
    $('.user-item').removeClass('active');
    event.currentTarget.classList.add('active');
    
    $('#messages').empty();
    
    fetch(`/get_history/${userId}`)
        .then(res => res.json())
        .then(data => {
            data.forEach(msg => renderizarMensaje(msg.sender, msg.text, msg.img, msg.is_me));
        });
}

function renderizarMensaje(sender, text, image, isMe) {
    const css = isMe ? 'my-message' : 'other-message';
    const html = `
        <div class="chat-main ${css}">
            ${!isMe ? `<img src="${image}" class="user_images">` : ''}
            <div class="chat-content-body">
                <span>${sender}</span>
                <li class="chat-box"><p>${text}</p></li>
            </div>
            ${isMe ? `<img src="${image}" class="user_images">` : ''}
        </div>`;
    $('#messages').append(html);
}

socket.on('receive_private_message', (msg) => {
    renderizarMensaje(msg.sender, msg.message, msg.img, msg.sender === currentUsername);
});

$(document).ready(function() {
    $("form").keydown(function(e) {
        if (e.which === 13) {
            e.preventDefault();
            let valor = $('#my_message').val().trim();
            if (valor !== '' && currentReceiverId) {
                socket.emit('private_message', { 'receiver_id': currentReceiverId, 'message': valor });
                $('#my_message').val('');
            }
        }
    });
});
