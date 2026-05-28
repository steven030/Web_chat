// chat_messages.js
const socket = io();

socket.on('message', function(msg) {
    const username = msg['username'];
    let menssage = msg['message'];
    let image = msg['img'];
    let _alert = msg['alert'];
    console.log(msg);

    let mensaje = () => {
        if (_alert == 'false') {
            
            // 1. Validamos en vivo si el mensaje proviene de ti mismo
            const isMe = (username === window.currentUser);
            
            // 2. Asignamos la clase CSS correspondiente para Flexbox
            const messageClass = isMe ? 'my-message' : 'other-message';
            
            // 3. Estructura HTML para el contenedor del avatar
            const avatarHTML = `
                <div class="chat-avatar-wrapper">
                    <img class="user_images" src="static/source/uploads/${image}" alt="${username}">
                </div>`;
            
            let htmlContent = '';
            
            // 4. Armamos los bloques respetando el orden visual exacto
            if (isMe) {
                // Si soy yo: Burbuja de texto primero, Avatar a la derecha
                htmlContent = `
                    <div class="chat-main ${messageClass} non-selectable">
                        <div class="chat-content-body">
                            <span class="chat-username">${username}</span>
                            <li class="chat-box">
                                <p id="content">${menssage}</p>
                            </li>
                        </div>
                        ${avatarHTML}
                    </div>`;
            } else {
                // Si es otra persona: Avatar a la izquierda, luego burbuja de texto
                htmlContent = `
                    <div class="chat-main ${messageClass} non-selectable">
                        ${avatarHTML}
                        <div class="chat-content-body">
                            <span class="chat-username">${username}</span>
                            <li class="chat-box">
                                <p id="content">${menssage}</p>
                            </li>
                        </div>
                    </div>`;
            }

            // 5. Inyectamos el nodo dinámico al final de la lista
            $('#messages').append(htmlContent);
            
            // 6. Ejecutamos los efectos de sonido y scroll del archivo de estilos
            setTimeout(sound('mensaje'), 300);
            window.scrollDiv();

        } else if (_alert == 'true') {
            setTimeout(sound('notificacion'), 300);
            $('#messages').append(`<div id="content-notify" class="non-selectable"><p id="notify">${username}${menssage}</p></div>`);
            window.scrollDiv();
        }
    };

    setTimeout(mensaje, 50);
});

// Mantén aquí abajo tus funciones de reproducción de sound() y los listeners de keydown...
