document.addEventListener('DOMContentLoaded', function() {
    // Seleziona gli elementi DOM
    const chatButton = document.getElementById('chatButton');
    const chatContainer = document.getElementById('chatContainer');
    const chatClose = document.getElementById('chatClose');
    const chatExpandBtn = document.getElementById('chatExpandBtn'); // Nuovo ID
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');
    const chatMessages = document.getElementById('chatMessages');
    const chatSavedToggle = document.getElementById('chatSavedToggle'); // Nuovo elemento per le chat salvate
    let chatHistory = [];
    let savedChatsPanel = null; // Verrà creato dinamicamente
    let savedChats = []; // Sarà popolato con le chat salvate
    
    // Verifica che gli elementi DOM necessari esistano
    if (!chatButton || !chatContainer || !chatClose || !chatExpandBtn || !chatInput || !chatSend || !chatMessages) {
        console.error("Alcuni elementi DOM della chat non sono stati trovati:", {
            chatButton, chatContainer, chatClose, chatExpandBtn, chatInput, chatSend, chatMessages
        });
        return; // Esci se mancano elementi essenziali
    }
    
    console.log("Elementi DOM della chat trovati correttamente");
    
    // Esponi la cronologia della chat e una funzione per aggiornarla a livello globale
    window.chatHistory = chatHistory;
    window.updateChatHistory = function(newHistory) {
        chatHistory = newHistory;
    };
    
    // Apri chat quando si clicca sul pulsante
    chatButton.addEventListener('click', function() {
        console.log("Chat button clicked");
        chatContainer.classList.add('active'); // Changed 'visible' to 'active' to match CSS class
        chatButton.classList.add('hidden');
        
        // Se è la prima apertura, aggiungi messaggio di benvenuto
        if (chatMessages.children.length === 0) {
            addMessage("Ciao! Sono l'assistente virtuale di Ristrutturazioni Morcianesi. Come posso aiutarti con il tuo preventivo?", 'received');
        }
    });
    
    // Chiudi chat quando si clicca sul pulsante di chiusura
    chatClose.addEventListener('click', function() {
        console.log("Chat close clicked");
        chatContainer.classList.remove('active'); // Changed 'visible' to 'active' to match CSS class
        chatContainer.classList.remove('expanded');
        chatButton.classList.remove('hidden');
        
        // Resetto l'icona del pulsante di espansione
        chatExpandBtn.innerHTML = '<i class="fas fa-expand-alt"></i>';
        chatExpandBtn.setAttribute('title', 'Espandi chat');
        chatExpandBtn.setAttribute('data-action', 'expand');
    });
    
    // Gestione del pulsante per visualizzare le chat salvate
    if (chatSavedToggle) {
        chatSavedToggle.addEventListener('click', function() {
            toggleSavedChatsPanel();
        });
    }
    
    // Funzione per creare e mostrare il pannello delle chat salvate
    function toggleSavedChatsPanel() {
        // Se il pannello non esiste ancora, crealo
        if (!savedChatsPanel) {
            createSavedChatsPanel();
        }
        
        // Altrimenti, toggle la visibilità del pannello
        if (savedChatsPanel.classList.contains('active')) {
            savedChatsPanel.classList.remove('active');
        } else {
            // Carica le chat salvate dall'API e poi mostra il pannello
            loadSavedChats().then(() => {
                savedChatsPanel.classList.add('active');
            });
        }
    }
    
    // Funzione per creare il pannello delle chat salvate
    function createSavedChatsPanel() {
        savedChatsPanel = document.createElement('div');
        savedChatsPanel.className = 'saved-chats-panel';
        
        // Creare l'intestazione del pannello
        const header = document.createElement('div');
        header.className = 'saved-chats-header';
        
        const title = document.createElement('h4');
        title.textContent = 'Chat Salvate';
        
        const closeBtn = document.createElement('button');
        closeBtn.innerHTML = '<i class="fas fa-times"></i>';
        closeBtn.title = "Chiudi";
        closeBtn.addEventListener('click', () => {
            savedChatsPanel.classList.remove('active');
        });
        
        header.appendChild(title);
        header.appendChild(closeBtn);
        
        // Creare la lista delle chat
        const chatsList = document.createElement('div');
        chatsList.className = 'saved-chats-list';
        chatsList.id = 'savedChatsList';
        
        // Aggiungi tutto al pannello
        savedChatsPanel.appendChild(header);
        savedChatsPanel.appendChild(chatsList);
        
        // Aggiungi il pannello al container della chat
        chatContainer.appendChild(savedChatsPanel);
    }
    
    // Funzione per caricare le chat salvate dall'API
    async function loadSavedChats() {
        const chatsList = document.getElementById('savedChatsList');
        if (!chatsList) return;
        
        chatsList.innerHTML = '<div class="loading-spinner"><i class="fas fa-spinner fa-spin"></i> Caricamento...</div>';
        
        try {
            // Crea un token CSRF per la richiesta
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            
            // Ottieni le chat salvate dal server
            const response = await fetch('/api/saved-chats', {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error('Errore nel caricamento delle chat');
            }
            
            const data = await response.json();
            savedChats = data.chats || [];
            
            // Pulisci la lista
            chatsList.innerHTML = '';
            
            // Se non ci sono chat salvate
            if (savedChats.length === 0) {
                chatsList.innerHTML = `
                    <div class="no-saved-chats">
                        <i class="fas fa-comment-slash"></i>
                        <p>Nessuna chat salvata</p>
                        <small>Le chat verranno salvate automaticamente quando chiudi la conversazione.</small>
                    </div>
                `;
                return;
            }
            
            // Popola la lista con le chat salvate
            savedChats.forEach(chat => {
                const chatItem = document.createElement('div');
                chatItem.className = 'saved-chat-item';
                chatItem.dataset.id = chat.id;
                
                const title = document.createElement('div');
                title.className = 'saved-chat-title';
                title.textContent = chat.title || 'Chat del ' + new Date(chat.created_at).toLocaleDateString();
                
                const date = document.createElement('div');
                date.className = 'saved-chat-date';
                date.textContent = new Date(chat.created_at).toLocaleString();
                
                const actions = document.createElement('div');
                actions.className = 'saved-chat-actions';
                
                const loadBtn = document.createElement('button');
                loadBtn.innerHTML = '<i class="fas fa-folder-open"></i> Apri';
                loadBtn.addEventListener('click', () => loadChat(chat.id));
                
                const deleteBtn = document.createElement('button');
                deleteBtn.innerHTML = '<i class="fas fa-trash"></i> Elimina';
                deleteBtn.addEventListener('click', (e) => {
                    e.stopPropagation();
                    deleteChat(chat.id);
                });
                
                actions.appendChild(loadBtn);
                actions.appendChild(deleteBtn);
                
                chatItem.appendChild(title);
                chatItem.appendChild(date);
                chatItem.appendChild(actions);
                
                // Aggiungi evento di click all'intero elemento per caricare la chat
                chatItem.addEventListener('click', () => loadChat(chat.id));
                
                chatsList.appendChild(chatItem);
            });
            
        } catch (error) {
            console.error('Errore nel caricamento delle chat:', error);
            chatsList.innerHTML = `
                <div class="error-message">
                    <i class="fas fa-exclamation-circle"></i>
                    <p>Errore nel caricamento delle chat</p>
                    <small>Si è verificato un problema. Riprova più tardi.</small>
                </div>
            `;
        }
    }
    
    // Funzione per caricare una chat specifica
    async function loadChat(chatId) {
        try {
            // Crea un token CSRF per la richiesta
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            
            // Ottieni la chat dal server
            const response = await fetch(`/api/saved-chats/${chatId}`, {
                method: 'GET',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error('Errore nel caricamento della chat');
            }
            
            const data = await response.json();
            
            if (data.success && data.messages) {
                // Pulisci la chat attuale
                chatMessages.innerHTML = '';
                chatHistory = [];
                
                // Carica i messaggi
                data.messages.forEach(msg => {
                    // Aggiungi il messaggio alla UI
                    addMessage(msg.content, msg.role === 'user' ? 'sent' : 'received');
                    
                    // Aggiorna la cronologia della chat
                    chatHistory.push({
                        role: msg.role,
                        content: msg.content
                    });
                });
                
                // Chiudi il pannello delle chat salvate
                savedChatsPanel.classList.remove('active');
            } else {
                throw new Error('Dati della chat non validi');
            }
        } catch (error) {
            console.error('Errore nel caricamento della chat:', error);
            alert('Non è stato possibile caricare la chat. Riprova più tardi.');
        }
    }
    
    // Funzione per eliminare una chat
    async function deleteChat(chatId) {
        if (!confirm('Sei sicuro di voler eliminare questa chat?')) return;
        
        try {
            // Crea un token CSRF per la richiesta
            const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
            
            // Elimina la chat dal server
            const response = await fetch(`/api/saved-chats/${chatId}`, {
                method: 'DELETE',
                headers: {
                    'X-CSRFToken': csrfToken
                }
            });
            
            if (!response.ok) {
                throw new Error('Errore nell\'eliminazione della chat');
            }
            
            const data = await response.json();
            
            if (data.success) {
                // Ricarica la lista delle chat
                loadSavedChats();
            } else {
                throw new Error('Eliminazione non riuscita');
            }
        } catch (error) {
            console.error('Errore nell\'eliminazione della chat:', error);
            alert('Non è stato possibile eliminare la chat. Riprova più tardi.');
        }
    }
    
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
        
        // Crea il div per il contenuto del messaggio
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        // Formatta il testo con supporto per markdown semplice
        let formattedText = text
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');
        
        contentDiv.innerHTML = formattedText;
        
        // Crea il div per l'avatar
        const avatarDiv = document.createElement('div');
        avatarDiv.className = 'message-avatar';
        
        // Aggiungi sia il contenuto che l'avatar al messaggio
        messageDiv.appendChild(contentDiv);
        messageDiv.appendChild(avatarDiv);
        
        // Aggiungi l'elemento al container
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