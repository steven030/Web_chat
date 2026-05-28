const socket = io();
const currentUsername = window.currentUser || "";
let currentReceiverId = null; // Variable global para el ID del destinatario

// 1. Conexión y Unión a sala privada
socket.on('connect', () => {
    console.log("Conectado. Uniéndose a sala privada...");
    socket.emit('join_private');
});

// 2. Función para seleccionar usuario (Llamada desde el HTML)
function selectUser(userId, username) {
    currentReceiverId = userId;
    
    // UI: Resaltar seleccionado
    $('.user-item').removeClass('active');
    event.currentTarget.classList.add('active');
    
    // Limpiar pantalla actual
    $('#messages').empty();
    
    // Cargar historial dinámicamente desde Flask
    fetch(`/get_history/${userId}`)
        .then(response => response.json())
        .then(data => {
            data.forEach(msg => {
                renderizarMensaje(msg.sender, msg.text, msg.img, msg.is_me);
            });
            if (typeof window.scrollDiv === "function") window.scrollDiv();
        });
}

// 3. Renderizado de mensajes (Usado tanto por historial como por socket)
function renderizarMensaje(sender, text, image, isMe) {
    const messageClass = isMe ? 'my-message' : 'other-message';
    const avatarSrc = (image && image.startsWith('http')) ? image : `static/source/uploads/${image}`;
    
    const avatarHTML = `
        <div class="chat-avatar-wrapper">
            <img class="user_images" src="${avatarSrc}" alt="${sender}">
        </div>`;

    const htmlContent = isMe ? `
        <div class="chat-main ${messageClass} non-selectable">
            <div class="chat-content-body">
                <span class="chat-username">${sender}</span>
                <li class="chat-box"><p id="content">${text}</p></li>
            </div>
            ${avatarHTML}
        </div>` : `
        <div class="chat-main ${messageClass} non-selectable">
            ${avatarHTML}
            <div class="chat-content-body">
                <span class="chat-username">${sender}</span>
                <li class="chat-box"><p id="content">${text}</p></li>
            </div>
        </div>`;

    $('#messages').append(htmlContent);
}

// 4. Escuchar mensajes nuevos en tiempo real
socket.on('receive_private_message', function(msg) {
    // msg viene con {sender, message, img}
    const isMe = (msg.sender === currentUsername);
    renderizarMensaje(msg.sender, msg.message, msg.img, isMe);
    
    sound('mensaje');
    if (typeof window.scrollDiv === "function") window.scrollDiv();
});

// 5. Manejo de Sonidos
let sound = (param) => {
    let audio = new Audio(param === 'mensaje' ? "static/sounds/mensaje-sound.mp3" : "static/sounds/ALERT_29.mp3");
    audio.volume = 0.1;
    audio.play();
};

// 6. Control de Teclado
$(document).ready(function() {
    var pulsado = false;
    $("form").keydown(function(e) {
        if (pulsado) return false;
        
        if (e.which === 13) {
            e.preventDefault();
            let valorInput = $('#my_message').val().trim();
            
            if (valorInput !== '' && currentReceiverId) {
                pulsado = true;
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
