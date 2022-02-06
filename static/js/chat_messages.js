const socket = io();






socket.on('message',function(msg){


	const username = msg['username'];
	let menssage = msg['message'];
	let image = msg['img']
	let _alert = msg['alert']
	console.log(msg)

	let mensaje = ()=>{
		if(_alert == 'false'){

			$('#messages').append(`<div class="chat-main" class="non-selectable"> <img class="user_images" src="static/source/uploads/${image}" alt="${username}"> <p id="user"> ${username} </p> <li class ="chat-box"> ` +'<br> <p id="content">' + menssage + '</p> <br> </li> <br>');
			setTimeout(sound('mensaje'),300);
			var div = document.getElementById('sub-message');
			div.scrollTop = '9999';


		}else if(_alert == 'true'){
			setTimeout(sound('notificacion'),300);
			$('#messages').append(`<div id="content-notify" class="non-selectable"> <p id="notify">` + username + menssage + `</p></div>`);
			var div = document.getElementById('sub-message');
			div.scrollTop = '9999';
		}
	};

	setTimeout(mensaje,50);







	
	
});

let sound = (param)=>{
	if(param == 'mensaje'){
		let etiquetaAudio = document.createElement("audio")
		etiquetaAudio.setAttribute("src", "static/sounds/mensaje-sound.mp3")
		etiquetaAudio.volume = 0.1;
		etiquetaAudio.play()
	}else if(param == 'notificacion'){
		let etiquetaAudio = document.createElement("audio")
		etiquetaAudio.setAttribute("src", "static/sounds/ALERT_29.mp3")
		etiquetaAudio.volume = 0.1;
		etiquetaAudio.play()
	}

}




socket.on('connect',()=>{
	
})
socket.on('disconnect',()=>{
	console.log(socket.connected)
	
})
socket.on('new_message',(data)=>{
	alert(`nuevo mensaje ${data}`)
})


$(document).ready(function() {
	var pulsado = false;
    $("form").keydown(function(e) {

    	if(pulsado) return false;
        if (e.which === 13) {
        	
        	if($('#my_message').val() != '' && $('#my_message').val() != null ){
           		socket.send($('#my_message').val());
				$('#my_message').val(' ');
			}
			pulsado = true;
			return false;
        }
    })
    .keyup(function(){
		 pulsado = false;
	});
});


// $('#send').on('click', function(){
// 	socket.send($('#my_message').val());
// 	$('#my_message').val(' ');


// });

// $('#reply').on('click', function(){
// 	socket.send($('#my_message').val());
// 	$('#my_message').val(' ');

// });

window.onload = ()=>{

	scrollDiv();


}
let scrollDiv = ()=>{

    var div = document.getElementById('sub-message');
    div.scrollTop = '1500';
 
};

