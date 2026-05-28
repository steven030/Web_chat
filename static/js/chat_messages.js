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
    
    // DEFINIMOS EL COMPONENTE AVATAR CON EL CONTENEDOR CORRECTO
    const avatarHTML = `
        <div class="chat-avatar-wrapper">
            <img src="${image}" class="user_images">
        </div>`;

    const html = `
        <div class="chat-main ${css}">
            ${!isMe ? avatarHTML : ''}
            <div class="chat-content-body">
                <span class="chat-username">${sender}</span>
                <li class="chat-box"><p>${text}</p></li>
            </div>
            ${isMe ? avatarHTML : ''}
        </div>`;
        
    $('#messages').append(html);
}

socket.on('receive_private_message', (msg) => {
    renderizarMensaje(msg.sender, msg.message, msg.img, msg.sender === currentUsername);
    // Opcional: auto-scroll al final después de recibir
    $('#sub-message').scrollTop($('#sub-message')[0].scrollHeight);
});

$(document).ready(function() {
    // Escucha el input directamente, no el form para evitar problemas de submit
    $('#my_message').keydown(function(e) {
        if (e.which === 13) {
            e.preventDefault();
            let valor = $(this).val().trim();
            if (valor !== '' && currentReceiverId) {
                socket.emit('private_message', { 'receiver_id': currentReceiverId, 'message': valor });
                $(this).val('');
            } else if (!currentReceiverId) {
                alert("Selecciona un usuario primero");
            }
        }
    });
});
