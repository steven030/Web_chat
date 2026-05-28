// chat_style.js

// Definimos el usuario logueado leyendo la variable global expuesta en el HTML
window.currentUser = window.currentUser || "";

// Función utilitaria para forzar el scroll al fondo del contenedor
window.scrollDiv = () => {
    const div = document.getElementById('sub-message');
    if (div) {
        div.scrollTop = div.scrollHeight; // Baja matemáticamente al último pixel
    }
};

// Asegurar que el scroll se ejecute al cargar la ventana por completo
window.onload = () => {
    window.scrollDiv();
};
