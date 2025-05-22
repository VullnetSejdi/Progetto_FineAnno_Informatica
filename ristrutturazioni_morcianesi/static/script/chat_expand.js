// Script dedicato all'espansione della chat - versione semplificata
document.addEventListener('DOMContentLoaded', function() {
    const chatContainer = document.getElementById('chatContainer');
    const chatExpandBtn = document.getElementById('chatExpandBtn');
    const chatMessages = document.getElementById('chatMessages');
    let isExpanded = false;
    
    if (!chatExpandBtn || !chatContainer) return; // Esci se gli elementi non esistono
    
    // Aggiungi evento al pulsante per toggleare la classe expanded
    chatExpandBtn.addEventListener('click', function(event) {
        event.preventDefault();
        event.stopPropagation();
        
        // Semplicemente togglea una classe CSS per l'espansione
        chatContainer.classList.toggle('expanded');
        isExpanded = !isExpanded;
        
        // Aggiorna l'icona in base allo stato
        if (isExpanded) {
            chatExpandBtn.innerHTML = '<i class="fas fa-compress-alt"></i>';
            chatExpandBtn.setAttribute('title', 'Riduci chat');
        } else {
            chatExpandBtn.innerHTML = '<i class="fas fa-expand-alt"></i>';
            chatExpandBtn.setAttribute('title', 'Espandi chat');
        }
        
        // Scorri verso il basso dopo l'espansione/riduzione
        setTimeout(function() {
            if (chatMessages) {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }
        }, 300);
        
        return false;
    });
});