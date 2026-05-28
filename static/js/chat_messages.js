const socket = io();
const currentUsername = window.currentUser || "";

// 1. Conexión y Unión a sala privada
socket.on('connect', () => {
    console.log("Conectado. Uniéndose a sala privada...");
    socket.emit('join_private');
});

// 2. Escuchar mensajes privados
socket.on('receive_private_message', function(msg) {
    const sender = msg['sender'];
    const messageText = msg['message'];
    const image = msg['img'];

    const isMe = (sender === currentUsername);
    const messageClass = isMe ? 'my-message' : 'other-message';
    
    // Si la imagen viene de ImageKit, no uses el prefijo local
    const avatarSrc = image.startsWith('http') ? image : `static/source/uploads/${image}`;
    
    const avatarHTML = `
        <div class="chat-avatar-wrapper">
            <img class="user_images" src="${avatarSrc}" alt="${sender}">
        </div>`;

    const htmlContent = isMe ? `
        <div class="chat-main ${messageClass} non-selectable">
            <div class="chat-content-body">
                <span class="chat-username">${sender}</span>
                <li class="chat-box"><p id="content">${messageText}</p></li>
            </div>
            ${avatarHTML}
        </div>` : `
        <div class="chat-main ${messageClass} non-selectable">
            ${avatarHTML}
            <div class="chat-content-body">
                <span class="chat-username">${sender}</span>
                <li class="chat-box"><p id="content">${messageText}</p></li>
            </div>
        </div>`;

    $('#messages').append(htmlContent);
    sound('mensaje');
    if (typeof window.scrollDiv === "function") window.scrollDiv();
});

// 3. Manejo de Sonidos
let sound = (param) => {
    let audio = new Audio(param === 'mensaje' ? "static/sounds/mensaje-sound.mp3" : "static/sounds/ALERT_29.mp3");
    audio.volume = 0.1;
    audio.play();
};

// 4. Control de Teclado (Envío de mensaje privado)
$(document).ready(function() {
    var pulsado = false;
    $("form").keydown(function(e) {
        if (pulsado) return false;
        
        if (e.which === 13) {
            e.preventDefault();
            let valorInput = $('#my_message').val().trim();
            
            if (valorInput !== '' && currentReceiverId) {
                pulsado = true;
                // ENVIAR MENSAJE PRIVADO
                socket.emit('private_message', {
                    'receiver_id': currentReceiverId,
                    'message': valorInput
                });
                $('#my_message').val('');
            } else if (!currentReceiverId) {
                alert("Selecciona un usuario de la lista primero.");
            }
            return false;
        }
    }).keyup(() => { pulsado = false; });
});
