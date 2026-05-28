const socket = io();

// CAPTURAR EL USUARIO ACTUAL
// Usamos la variable global que definimos previamente en el HTML
const currentUsername = window.currentUser || ""; 

socket.on('message', function(msg){

	const username = msg['username'];
	let menssage = msg['message'];
	let image = msg['img'];
	let _alert = msg['alert'];
	console.log(msg);

	let procesarMensaje = ()=>{
		if(_alert == 'false'){

			// 1. Validamos en vivo si el mensaje proviene de ti mismo
			const isMe = (username === currentUsername);
			
			// 2. Asignamos la clase condicional para el CSS Flexbox
			const messageClass = isMe ? 'my-message' : 'other-message';
			
			// 3. Estructura base para el contenedor del avatar
			const avatarHTML = `
				<div class="chat-avatar-wrapper">
					<img class="user_images" src="static/source/uploads/${image}" alt="${username}">
				</div>`;
			
			let htmlContent = '';
			
			// 4. Armamos los bloques respetando el orden visual de burbujas
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
				// Si es otro usuario: Avatar a la izquierda, luego Burbuja de texto
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

			// 5. Inyectamos el nodo dinámico al final de la lista de mensajes
			$('#messages').append(htmlContent);

			setTimeout(sound('mensaje'), 300);
			
			// Ejecutamos la función global de scroll de forma segura
			if (typeof window.scrollDiv === "function") {
				window.scrollDiv();
			}

		} else if(_alert == 'true') {
			setTimeout(sound('notificacion'), 300);
			$('#messages').append(`<div id="content-notify" class="non-selectable"> <p id="notify">` + username + menssage + `</p></div>`);
			
			if (typeof window.scrollDiv === "function") {
				window.scrollDiv();
			}
		}
	};

	setTimeout(procesarMensaje, 50);
});

let sound = (param)=>{
	if(param == 'mensaje'){
		let etiquetaAudio = document.createElement("audio")
		etiquetaAudio.setAttribute("src", "static/sounds/mensaje-sound.mp3")
		etiquetaAudio.volume = 0.1;
		etiquetaAudio.play()
	} else if(param == 'notificacion'){
		let etiquetaAudio = document.createElement("audio")
		etiquetaAudio.setAttribute("src", "static/sounds/ALERT_29.mp3")
		etiquetaAudio.volume = 0.1;
		etiquetaAudio.play()
	}
}

socket.on('connect', () => {
	console.log("Conectado exitosamente al servidor de websockets.");
});

socket.on('disconnect', () => {
	console.log(socket.connected);
});

socket.on('new_message', (data) => {
	alert(`nuevo mensaje ${data}`);
});

// CONTROL DE TECLADO (ENTER) REPARADO
$(document).ready(function() {
	var pulsado = false;
    $("form").keydown(function(e) {
        if(pulsado) return false;
        
        if (e.which === 13) {
            e.preventDefault(); // Evita que el formulario recargue la página completa
            
            let valorInput = $('#my_message').val().trim(); // Limpiamos espacios vacíos
            
            if(valorInput != '' && valorInput != null ){
                pulsado = true; // Bloqueamos ráfagas de Enter
                socket.send(valorInput); // Enviamos el texto limpio
                $('#my_message').val(''); // Limpieza absoluta a vacío
            }
            return false;
        }
    })
    .keyup(function(){
		 pulsado = false; // Desbloqueamos la bandera al soltar la tecla
	});
});
