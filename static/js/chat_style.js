// chat_style.js

// 1. Definimos el usuario logueado de forma segura
window.currentUser = window.currentUser || "";

// 2. Función utilitaria para forzar el scroll al fondo del contenedor
window.scrollDiv = () => {
    const div = document.getElementById('sub-message');
    if (div) {
        div.scrollTop = div.scrollHeight; // Baja matemáticamente al último píxel
    }
};

// 3. REGISTRO SEGURO DEL SCROLL (Sin pisar otros scripts)
// Usamos un EventListener nativo para que se ejecute en paralelo sin bloquear los sockets
window.addEventListener('load', () => {
    window.scrollDiv();
});
