// chat_style.js

// 1. Definimos el usuario logueado leyendo la variable global expuesta en el HTML
window.currentUser = window.currentUser || "";

// 2. Función utilitaria para forzar el scroll al fondo del contenedor
window.scrollDiv = () => {
    const div = document.getElementById('sub-message');
    if (div) {
        div.scrollTop = div.scrollHeight; // Baja matemáticamente al último píxel
    }
};

// 3. Asegurar que el scroll se ejecute al cargar la ventana por completo sin bloquear los sockets
window.addEventListener('load', () => {
    window.scrollDiv();
});
