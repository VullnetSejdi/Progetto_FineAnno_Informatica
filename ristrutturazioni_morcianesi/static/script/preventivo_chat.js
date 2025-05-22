// Script per la gestione della chat del preventivo rapido

// Variabili globali
const isPopup = window.opener && !window.opener.closed;
let chatHistory = [];
let isChatSaved = false;
let currentChatId = null;
let hasSavedChats = false;
let autoSaveTimer = null;
const AUTO_SAVE_DELAY = 10000; // 10 secondi di inattività prima del salvataggio automatico

// Inizializzazione
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM fully loaded, initializing chat...');
    
    // Elementi DOM
    const chatMessages = document.getElementById('chatMessages');
    const chatInput = document.getElementById('chatInput');
    const chatSend = document.getElementById('chatSend');
    const chatSaveBtn = document.getElementById('chatSave');
    const chatSaveLoginBtn = document.getElementById('chatSaveLogin');
    const saveConfirmation = document.getElementById('saveConfirmation');
    
    // Elementi per il pannello delle chat salvate
    const chatHistoryButton = document.getElementById('chatHistoryButton');
    const savedChatsPanel = document.getElementById('savedChatsPanel');
    const savedChatsOverlay = document.getElementById('savedChatsOverlay');
    const savedChatsClose = document.getElementById('savedChatsClose');
    const savedChatList = document.getElementById('savedChatList');
    const newChatBtn = document.getElementById('newChatBtn');
    const chatSavedToggle = document.getElementById('chatSavedToggle');
    const chatQuickAccess = document.getElementById('chatQuickAccess');
    const savedChatsBanner = document.getElementById('savedChatsBanner');
    const viewSavedChatsBtn = document.getElementById('viewSavedChatsBtn');
    const closeBannerBtn = document.getElementById('closeBannerBtn');
    const chatNotificationIndicator = document.getElementById('chatNotificationIndicator');
    
    // Variabili di stato
    let conversationId = null;
    let isTyping = false;
    let lastActivity = Date.now();
    let messagesHistory = [];
    let savedChats = [];
    
    // Token CSRF per le richieste
    const csrfTokenMeta = document.querySelector('meta[name="csrf-token"]');
    const csrfToken = csrfTokenMeta ? csrfTokenMeta.getAttribute('content') : '';
    
    if(!csrfToken) {
        console.error('CSRF token not found! Chat functionality may not work properly.');
    }
    
    // =================
    // GESTIONE MESSAGGI
    // =================
    
    // Funzione per inviare un messaggio
    function sendMessage() {
        const messageText = chatInput.value.trim();
        if (!messageText) return;
        
        console.log('Sending message:', messageText);
        
        // Aggiungi il messaggio alla UI
        addMessageToUI('sent', messageText);
        
        // Pulisci l'input
        chatInput.value = '';
        
        // Mostra l'indicatore di digitazione
        showTyping();
        
        // Aggiorna l'ultimo momento di attività
        updateLastActivity();
        
        // Invia il messaggio al server
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                message: messageText,
                conversation_id: conversationId
            })
        })
        .then(response => response.json())
        .then(data => {
            // Nascondi l'indicatore di digitazione
            hideTyping();
            
            if (data.success) {
                // Aggiorna l'ID della conversazione
                conversationId = data.conversation_id;
                
                // Aggiungi la risposta alla UI
                addMessageToUI('received', data.response);
                
                // Avvia il timer per il salvataggio automatico
                if (autoSaveTimer) clearTimeout(autoSaveTimer);
                autoSaveTimer = setTimeout(autoSaveChat, AUTO_SAVE_DELAY); // 10 secondi
            } else {
                addMessageToUI('error', 'Si è verificato un errore. Riprova più tardi.');
            }
        })
        .catch(error => {
            console.error('Errore:', error);
            hideTyping();
            addMessageToUI('error', 'Errore di connessione. Verifica la tua connessione e riprova.');
        });
    }
    
    // Funzione per aggiungere un messaggio all'UI
    function addMessageToUI(type, content) {
        const message = document.createElement('div');
        message.classList.add('message', type);
        
        const messageContent = document.createElement('div');
        messageContent.classList.add('message-content');
        messageContent.textContent = content;
        
        message.appendChild(messageContent);
        chatMessages.appendChild(message);
        
        // Scorri alla fine della chat
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        // Memorizza il messaggio nella cronologia
        messagesHistory.push({
            type: type,
            content: content
        });
    }
    
    // Mostra indicatore di digitazione
    function showTyping() {
        if (isTyping) return;
        
        isTyping = true;
        const typingIndicator = document.createElement('div');
        typingIndicator.classList.add('typing-indicator');
        typingIndicator.id = 'typingIndicator';
        
        // Aggiungi i dot di digitazione
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            typingIndicator.appendChild(dot);
        }
        
        chatMessages.appendChild(typingIndicator);
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Nascondi indicatore di digitazione
    function hideTyping() {
        const typingIndicator = document.getElementById('typingIndicator');
        if (typingIndicator) {
            typingIndicator.remove();
            isTyping = false;
        }
    }
    
    // =================
    // SALVARE LE CHAT
    // =================
    
    // Funzione per salvare la chat manualmente
    function saveChat() {
        if (!conversationId || messagesHistory.length === 0) {
            showNotification('Non c\'è nulla da salvare!', 'info');
            return;
        }
        
        // Determina un titolo per la conversazione
        let title = '';
        
        // Cerca il primo messaggio dell'utente per usarlo come titolo
        for (const message of messagesHistory) {
            if (message.type === 'sent') {
                title = message.content.substring(0, 50) + (message.content.length > 50 ? '...' : '');
                break;
            }
        }
        
        // Se non ci sono messaggi dell'utente, usa un titolo generico
        if (!title) {
            title = 'Nuova conversazione';
        }
        
        fetch('/api/chat/save', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRF-Token': csrfToken
            },
            body: JSON.stringify({
                conversation_id: conversationId,
                title: title
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Mostra conferma
                showNotification('Conversazione salvata!', 'success');
                
                // Aggiorna lo stato del pulsante
                if (chatSaveBtn) {
                    chatSaveBtn.classList.add('saved');
                    setTimeout(() => {
                        const indicator = chatSaveBtn.querySelector('.chat-saved-indicator');
                        if (indicator) {
                            indicator.classList.add('flash');
                            setTimeout(() => {
                                indicator.classList.remove('flash');
                            }, 1000);
                        }
                    }, 100);
                }
                
                // Aggiorna l'elenco delle chat salvate
                loadSavedChats();
            } else {
                showNotification('Errore durante il salvataggio', 'error');
            }
        })
        .catch(error => {
            console.error('Errore:', error);
            showNotification('Errore di connessione', 'error');
        });
    }
    
    // Funzione per il salvataggio automatico
    function autoSaveChat() {
        // Verifica se ci sono abbastanza messaggi da salvare
        if (messagesHistory.length >= 2) {
            saveChat();
        }
    }
    
    // Mostra notifica
    function showNotification(message, type = 'success') {
        if (saveConfirmation) {
            saveConfirmation.textContent = message;
            saveConfirmation.className = 'save-confirmation ' + type;
            saveConfirmation.classList.add('visible');
            
            setTimeout(() => {
                saveConfirmation.classList.remove('visible');
            }, 3000);
        }
    }
    
    // Aggiorna il timestamp dell'ultima attività
    function updateLastActivity() {
        lastActivity = Date.now();
    }
    
    // ========================
    // GESTIONE CHAT SALVATE
    // ========================
    
    // Carica le chat salvate
    function loadSavedChats() {
        fetch('/api/chat/saved', {
            method: 'GET',
            headers: {
                'X-CSRF-Token': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.conversations) {
                savedChats = data.conversations;
                updateSavedChatsList();
                
                // Aggiorna l'indicatore di notifica
                if (chatNotificationIndicator) {
                    const count = savedChats.length;
                    
                    // Nascondi l'indicatore se non ci sono chat
                    if (count === 0) {
                        chatNotificationIndicator.style.display = 'none';
                    } else {
                        chatNotificationIndicator.style.display = 'block';
                        
                        // Aggiunge l'animazione di attenzione al pulsante di history
                        if (chatHistoryButton) {
                            chatHistoryButton.classList.add('attention-needed');
                            setTimeout(() => {
                                chatHistoryButton.classList.remove('attention-needed');
                            }, 3000);
                        }
                    }
                }
                
                // Mostra/nascondi il banner delle chat salvate
                if (savedChatsBanner) {
                    if (savedChats.length > 0 && !localStorage.getItem('bannerDismissed')) {
                        setTimeout(() => {
                            savedChatsBanner.classList.add('visible');
                        }, 2000);
                    }
                }
            }
        })
        .catch(error => {
            console.error('Errore nel caricamento delle chat:', error);
        });
    }
    
    // Aggiorna la lista delle chat salvate nella UI
    function updateSavedChatsList() {
        if (!savedChatList) return;
        
        // Svuota la lista
        savedChatList.innerHTML = '';
        
        if (savedChats.length === 0) {
            // Mostra il messaggio "nessuna chat salvata"
            const noChatsMessage = document.createElement('div');
            noChatsMessage.className = 'no-saved-chats';
            noChatsMessage.innerHTML = '<i class="fas fa-inbox"></i><p>Nessuna conversazione salvata</p>';
            savedChatList.appendChild(noChatsMessage);
            return;
        }
        
        // Ordina le chat per data (più recenti in cima)
        savedChats.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));
        
        // Crea un elemento per ogni chat
        savedChats.forEach(chat => {
            const chatItem = document.createElement('div');
            chatItem.className = 'saved-chat-item';
            if (chat.id === conversationId) {
                chatItem.classList.add('current');
            }
            
            // Formatta la data
            const chatDate = new Date(chat.timestamp);
            const formattedDate = formatDate(chatDate);
            
            // Determina l'anteprima del contenuto
            let preview = 'Nessun contenuto';
            if (chat.content && chat.content.length > 0) {
                const firstMessage = chat.content[0];
                preview = firstMessage.content.substring(0, 100) + (firstMessage.content.length > 100 ? '...' : '');
            }
            
            chatItem.innerHTML = `
                <h5>${chat.title || 'Conversazione senza titolo'}</h5>
                <div class="saved-chat-date">${formattedDate}</div>
                <div class="saved-chat-preview">${preview}</div>
                <div class="saved-chat-actions">
                    <button class="saved-chat-delete" data-id="${chat.id}" title="Elimina conversazione">
                        <i class="fas fa-trash"></i>
                    </button>
                </div>
            `;
            
            // Aggiungi l'evento click per caricare la chat
            chatItem.addEventListener('click', (e) => {
                // Se il click è sul pulsante elimina, non caricare la chat
                if (e.target.closest('.saved-chat-delete')) {
                    return;
                }
                loadChat(chat.id);
            });
            
            savedChatList.appendChild(chatItem);
        });
        
        // Aggiungi gli eventi per eliminare le chat
        const deleteButtons = document.querySelectorAll('.saved-chat-delete');
        deleteButtons.forEach(button => {
            button.addEventListener('click', (e) => {
                e.stopPropagation();
                const chatId = button.getAttribute('data-id');
                deleteChat(chatId);
            });
        });
    }
    
    // Carica una chat specifica
    function loadChat(chatId) {
        fetch(`/api/chat/${chatId}`, {
            method: 'GET',
            headers: {
                'X-CSRF-Token': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.conversation) {
                // Aggiorna l'ID della conversazione corrente
                conversationId = data.conversation.id;
                
                // Svuota la chat attuale
                chatMessages.innerHTML = '';
                messagesHistory = [];
                
                // Carica i messaggi
                if (data.conversation.content && data.conversation.content.length > 0) {
                    data.conversation.content.forEach(msg => {
                        addMessageToUI(msg.type, msg.content);
                    });
                }
                
                // Chiudi il pannello delle chat salvate
                closeSavedChatsPanel();
                
                // Aggiorna l'UI per indicare che questa è la chat corrente
                updateSavedChatsList();
                
                // Mostra notifica
                showNotification('Conversazione caricata!', 'info');
                
                // Se il pulsante salva è presente, aggiorna il suo stato
                if (chatSaveBtn) {
                    chatSaveBtn.classList.add('saved');
                }
            } else {
                showNotification('Errore nel caricamento della chat', 'error');
            }
        })
        .catch(error => {
            console.error('Errore:', error);
            showNotification('Errore di connessione', 'error');
        });
    }
    
    // Elimina una chat
    function deleteChat(chatId) {
        fetch(`/api/chat/${chatId}`, {
            method: 'DELETE',
            headers: {
                'X-CSRF-Token': csrfToken
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Se è la chat corrente, reimposta lo stato
                if (chatId === conversationId) {
                    // Crea una nuova conversazione
                    startNewChat();
                }
                
                // Aggiorna la lista delle chat
                loadSavedChats();
                
                // Mostra notifica
                showNotification('Conversazione eliminata', 'info');
            } else {
                showNotification('Errore durante l\'eliminazione', 'error');
            }
        })
        .catch(error => {
            console.error('Errore:', error);
            showNotification('Errore di connessione', 'error');
        });
    }
    
    // Avvia una nuova chat
    function startNewChat() {
        // Reimposta l'ID della conversazione
        conversationId = null;
        
        // Svuota i messaggi
        chatMessages.innerHTML = '';
        messagesHistory = [];
        
        // Aggiorna l'UI
        updateSavedChatsList();
        
        // Chiudi il pannello delle chat salvate
        closeSavedChatsPanel();
        
        // Se il pulsante salva è presente, aggiorna il suo stato
        if (chatSaveBtn) {
            chatSaveBtn.classList.remove('saved');
        }
    }
    
    // Formatta la data in un formato leggibile
    function formatDate(date) {
        const today = new Date();
        const yesterday = new Date(today);
        yesterday.setDate(today.getDate() - 1);
        
        // Se è oggi
        if (date.toDateString() === today.toDateString()) {
            return `Oggi alle ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        }
        
        // Se è ieri
        if (date.toDateString() === yesterday.toDateString()) {
            return `Ieri alle ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
        }
        
        // Altrimenti mostra la data completa
        return `${date.getDate().toString().padStart(2, '0')}/${(date.getMonth() + 1).toString().padStart(2, '0')}/${date.getFullYear()} - ${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`;
    }
    
    // ===================
    // UI INTERATTIVA
    // ===================
    
    // Mostra il pannello delle chat salvate
    function showSavedChatsPanel() {
        if (savedChatsPanel) {
            savedChatsPanel.classList.add('visible');
            if (savedChatsOverlay) {
                savedChatsOverlay.classList.add('visible');
            }
            document.body.style.overflow = 'hidden'; // Previene lo scrolling
        }
    }
    
    // Chiudi il pannello delle chat salvate
    function closeSavedChatsPanel() {
        if (savedChatsPanel) {
            savedChatsPanel.classList.remove('visible');
            if (savedChatsOverlay) {
                savedChatsOverlay.classList.remove('visible');
            }
            document.body.style.overflow = ''; // Ripristina lo scrolling
        }
    }
    
    // =====================
    // EVENT LISTENERS
    // =====================
    
    // Event listener per l'invio con il tasto Invio
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
    
    // Event listener per l'invio con il pulsante
    if (chatSend) {
        chatSend.addEventListener('click', sendMessage);
    }
    
    // Event listener per salvare la chat
    if (chatSaveBtn) {
        chatSaveBtn.addEventListener('click', saveChat);
    }
    
    // Event listener per gli utenti non autenticati
    if (chatSaveLoginBtn) {
        chatSaveLoginBtn.addEventListener('click', function() {
            // Reindirizza alla pagina di login
            window.location.href = '/login?next=' + encodeURIComponent(window.location.pathname);
        });
    }
    
    // Event listeners per il pannello delle chat salvate
    if (chatHistoryButton) {
        chatHistoryButton.addEventListener('click', function() {
            showSavedChatsPanel();
        });
    }
    
    if (savedChatsClose) {
        savedChatsClose.addEventListener('click', closeSavedChatsPanel);
    }
    
    if (savedChatsOverlay) {
        savedChatsOverlay.addEventListener('click', closeSavedChatsPanel);
    }
    
    if (newChatBtn) {
        newChatBtn.addEventListener('click', function() {
            startNewChat();
        });
    }
    
    // Event listener per i pulsanti del banner
    if (viewSavedChatsBtn) {
        viewSavedChatsBtn.addEventListener('click', function() {
            showSavedChatsPanel();
            // Nascondi il banner
            if (savedChatsBanner) {
                savedChatsBanner.classList.remove('visible');
                localStorage.setItem('bannerDismissed', 'true');
            }
        });
    }
    
    if (closeBannerBtn) {
        closeBannerBtn.addEventListener('click', function() {
            if (savedChatsBanner) {
                savedChatsBanner.classList.remove('visible');
                localStorage.setItem('bannerDismissed', 'true');
            }
        });
    }
    
    // Event listener per il toggle delle chat salvate nella navbar
    if (chatSavedToggle) {
        chatSavedToggle.addEventListener('click', showSavedChatsPanel);
    }
    
    // Event listener per il pulsante di accesso rapido
    if (chatQuickAccess) {
        chatQuickAccess.addEventListener('click', showSavedChatsPanel);
    }
    
    // Inizializza caricando le chat salvate se l'utente è autenticato
    if (chatHistoryButton || chatSaveBtn) {
        // L'utente è autenticato, carica le chat salvate
        loadSavedChats();
    }
    
    // Avvia una nuova chat
    startNewChat();
    
    // Aggiungi messaggio di benvenuto
    setTimeout(() => {
        addMessageToUI('received', 'Benvenuto al servizio di preventivo rapido! Come posso aiutarti con la tua ristrutturazione?');
    }, 500);
    
    console.log('Chat initialization complete!');
});