document.addEventListener('DOMContentLoaded', function() {
    const chatButton = document.getElementById('chatButton');
    const chatContainer = document.getElementById('chatContainer');
    const chatClose = document.getElementById('chatClose');
    const chatExpand = document.getElementById('chatExpand');
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');
    const chatMessages = document.getElementById('chatMessages');
    let chatHistory = [];
    let chatWindow = null;
    
    // Esponi la cronologia della chat e una funzione per aggiornarla a livello globale
    window.chatHistory = chatHistory;
    window.updateChatHistory = function(newHistory) {
        chatHistory = newHistory;
        // Opzionalmente, aggiorna anche l'interfaccia della chat incorporata
    };
    
    // Apri chat quando si clicca sul pulsante
    chatButton.addEventListener('click', function() {
        chatContainer.classList.add('active');
        chatButton.classList.add('hidden');
        
        // Se è la prima apertura, aggiungi messaggio di benvenuto
        if (chatMessages.children.length === 0) {
            addMessage("Ciao! Sono l'assistente virtuale di Ristrutturazioni Morcianesi. Come posso aiutarti con il tuo preventivo?", 'received');
        }
    });
    
    // Chiudi chat quando si clicca sul pulsante di chiusura
    chatClose.addEventListener('click', function() {
        chatContainer.classList.remove('active');
        chatButton.classList.remove('hidden');
    });
    
    // Apri la chat in una nuova finestra quando si clicca sul pulsante di espansione
    chatExpand.addEventListener('click', function() {
        const chatUrl = '/chat';
        const width = 400;
        const height = 600;
        const left = (window.innerWidth - width) / 2;
        const top = (window.innerHeight - height) / 2;
        
        // Chiudi la finestra precedente se esiste
        if (chatWindow && !chatWindow.closed) {
            chatWindow.focus();
        } else {
            // Apri una nuova finestra
            chatWindow = window.open(
                chatUrl,
                'chatWindow',
                `width=${width},height=${height},left=${left},top=${top},resizable=yes,scrollbars=yes`
            );
            
            // Chiudi la chat incorporata
            chatContainer.classList.remove('active');
            chatButton.classList.remove('hidden');
        }
    });
    
    // Invia messaggio quando si preme il pulsante invia
    chatSend.addEventListener('click', sendMessage);
    
    // Invia messaggio quando si preme Enter (ma non shift+enter)
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    function sendMessage() {
        const message = chatInput.value.trim();
        if (message) {
            // Aggiungi messaggio dell'utente
            addMessage(message, 'sent');
            chatInput.value = '';
            chatInput.disabled = true;
            
            // Aggiungi l'indicatore di digitazione
            const typingIndicator = document.createElement('div');
            typingIndicator.className = 'typing-indicator';
            typingIndicator.innerHTML = '<span></span><span></span><span></span>';
            chatMessages.appendChild(typingIndicator);
            chatMessages.scrollTop = chatMessages.scrollHeight;
            
            // Aggiorna la cronologia della chat
            chatHistory.push({
                "role": "user",
                "content": message
            });
            
            // Crea un token CSRF per la richiesta
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            
            // Invia al backend
            fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken
                },
                body: JSON.stringify({
                    message: message,
                    history: chatHistory.slice(-10) // Invia solo gli ultimi 10 messaggi
                }),
            })
            .then(response => response.json())
            .then(data => {
                // Rimuovi l'indicatore di digitazione
                const indicator = document.querySelector('.typing-indicator');
                if (indicator) {
                    indicator.remove();
                }
                
                chatInput.disabled = false;
                
                if (data.success) {
                    addMessage(data.message, 'received');
                    
                    // Aggiorna la cronologia della chat
                    chatHistory.push({
                        "role": "assistant",
                        "content": data.message
                    });
                } else {
                    addMessage("Mi dispiace, si è verificato un errore. Riprova più tardi.", 'received error');
                }
            })
            .catch(error => {
                console.error('Error:', error);
                
                // Rimuovi l'indicatore di digitazione
                const indicator = document.querySelector('.typing-indicator');
                if (indicator) {
                    indicator.remove();
                }
                
                chatInput.disabled = false;
                addMessage("Mi dispiace, non riesco a connettermi al server. Riprova più tardi.", 'received error');
            });
        }
    }
    
    function addMessage(text, type) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Formatta il testo con supporto per markdown semplice
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
        
        contentDiv.innerHTML = formattedText;
        messageDiv.appendChild(contentDiv);
        
        // Aggiungi l'elemento al container
        const chatMessages = document.getElementById('chatMessages');
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom con animazione fluida
        chatMessages.scrollTo({
            top: chatMessages.scrollHeight,
            behavior: 'smooth'
        });
        
        // Stagger animation (ritardo basato sul numero di messaggi)
        setTimeout(() => {
            messageDiv.style.animation = 'none'; // Reset animation
            void messageDiv.offsetWidth; // Force reflow
            messageDiv.style.animation = 'messageAppear 0.4s ease forwards';
        }, 50);
    }
});