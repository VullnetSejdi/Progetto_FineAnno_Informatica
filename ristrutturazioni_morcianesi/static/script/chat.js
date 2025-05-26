/**
 * Chat Principale - Sistema Completo di Chat con Salvataggio
 * Sistema completo per la gestione della chat principale
 */

// === CONFIGURAZIONE ===
// Leggi la configurazione dagli attributi del tag script
const currentScript = document.currentScript || document.querySelector('script[data-user-authenticated]');
const isLoggedIn = currentScript?.getAttribute('data-user-authenticated') === 'true';
const loginUrl = currentScript?.getAttribute('data-login-url') || '/login';
const csrfToken = currentScript?.getAttribute('data-csrf-token') || document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');

// === VARIABILI GLOBALI ===
const isPopup = window.opener && !window.opener.closed;
let chatHistory = [];
let isChatSaved = false;
let currentChatId = null;
let hasSavedChats = false;

// === FUNZIONI DI PERSISTENZA ===
function saveChatToStorage() {
    try {
        const chatData = {
            history: chatHistory,
            timestamp: new Date().toISOString(),
            currentChatId: currentChatId,
            isSaved: isChatSaved
        };
        localStorage.setItem('currentChatSession', JSON.stringify(chatData));
    } catch (error) {
        console.error('Errore nel salvare la chat in localStorage:', error);
    }
}

function loadChatFromStorage() {
    try {
        const savedData = localStorage.getItem('currentChatSession');
        if (savedData) {
            const chatData = JSON.parse(savedData);
            chatHistory = chatData.history || [];
            currentChatId = chatData.currentChatId || null;
            isChatSaved = chatData.isSaved || false;
            
            // Ripristina i messaggi se ce ne sono
            if (chatHistory.length > 0) {
                restoreChatMessages();
            }
        }
    } catch (error) {
        console.error('Errore nel caricare la chat da localStorage:', error);
        chatHistory = [];
    }
}

function restoreChatMessages() {
    const chatMessagesContainer = document.getElementById('chatMessages');
    if (!chatMessagesContainer) return;
    
    chatMessagesContainer.innerHTML = '';
    window.isRestoringMessages = true;
    
    chatHistory.forEach(msg => {
        addMessage(msg.content, msg.role === 'user' ? 'sent' : 'received');
    });
    
    window.isRestoringMessages = false;
}

function syncWithDatabase() {
    if (!isLoggedIn) return;
    
    // Carica le chat salvate e verifica se quella attuale è già salvata
    fetch('/api/saved-chats', {
        method: 'GET',
        headers: {
            'X-CSRFToken': config.csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.chats && data.chats.length > 0) {
            // Verifica se la chat attuale è già nel database
            if (currentChatId) {
                const existingChat = data.chats.find(chat => chat.id === currentChatId);
                if (existingChat) {
                    // La chat esiste già nel database, aggiorna lo stato
                    isChatSaved = true;
                    const chatSaveBtn = document.getElementById('chatSave');
                    if (chatSaveBtn) {
                        chatSaveBtn.classList.add('saved');
                    }
                }
            }
        }
    })
    .catch(error => {
        console.error('Errore nella sincronizzazione:', error);
    });
}

// === GESTIONE MESSAGGI ===
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
    document.getElementById('chatMessages').appendChild(messageDiv);
    
    // Scroll to bottom con animazione fluida
    const chatMessagesContainer = document.getElementById('chatMessages');
    chatMessagesContainer.scrollTo({
        top: chatMessagesContainer.scrollHeight,
        behavior: 'smooth'
    });
    
    // Salva automaticamente in localStorage se non è un messaggio di ripristino
    if (!window.isRestoringMessages) {
        saveChatToStorage();
    }
}

function sendMessage() {
    const chatInput = document.getElementById('chatInput');
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
        document.getElementById('chatMessages').appendChild(typingIndicator);
        document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
        
        // Aggiorna la cronologia della chat
        chatHistory.push({
            "role": "user",
            "content": message
        });
        
        // Se la chat era stata salvata, aggiorniamo lo stato
        if (isChatSaved && currentChatId) {
            isChatSaved = false;
            const chatSaveBtn = document.getElementById('chatSave');
            if (chatSaveBtn) {
                chatSaveBtn.classList.remove('saved');
            }
        }
        
        // Invia al backend
        fetch('/api/chat', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': config.csrfToken
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
                
                // Se è un popup, aggiorna anche la cronologia nella finestra principale
                if (isPopup && window.opener.updateChatHistory) {
                    try {
                        window.opener.updateChatHistory(chatHistory);
                    } catch (error) {
                        console.error('Errore nell\'aggiornamento della cronologia:', error);
                    }
                }
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

// === GESTIONE CHAT SALVATE ===
function saveChat() {
    if (!isLoggedIn) {
        window.location.href = config.loginUrl;
        return;
    }
    
    // Se non ci sono messaggi da salvare, non fare nulla
    if (chatHistory.length <= 1) {
        showTemporaryMessage("Non c'è nulla da salvare", "error");
        return;
    }
    
    // Se la chat è già stata salvata e non è stata modificata, non fare nulla
    if (isChatSaved) {
        showTemporaryMessage("Questa conversazione è già stata salvata", "info");
        return;
    }
    
    // Prepara i dati da inviare
    const firstUserMessage = chatHistory.find(msg => msg.role === 'user')?.content || "Nuova conversazione";
    const title = firstUserMessage.substring(0, 50) + (firstUserMessage.length > 50 ? '...' : '');
    
    // Invia la richiesta per salvare la chat
    fetch('/api/save-chat', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': config.csrfToken
        },
        body: JSON.stringify({
            title: title,
            messages: chatHistory,
            chat_id: currentChatId // Invia null se è nuova, altrimenti l'ID per aggiornare
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Aggiorna il riferimento all'ID della chat
            currentChatId = data.chat_id;
            
            // Aggiorna l'interfaccia
            isChatSaved = true;
            const chatSaveBtn = document.getElementById('chatSave');
            if (chatSaveBtn) chatSaveBtn.classList.add('saved');
            
            // Mostra la conferma
            showSaveConfirmation();
            
            // Ricarica la lista delle chat salvate
            loadSavedChats();
            
            // Aggiorna localStorage
            saveChatToStorage();
        } else {
            showTemporaryMessage("Errore durante il salvataggio: " + data.error, "error");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showTemporaryMessage("Errore durante il salvataggio", "error");
    });
}

function loadSavedChats(checkForBanner = false) {
    if (!isLoggedIn) return;
    
    fetch('/api/saved-chats', {
        method: 'GET',
        headers: {
            'X-CSRFToken': config.csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        const savedChatList = document.getElementById('savedChatList');
        
        if (data.success && data.chats && data.chats.length > 0) {
            // Pulisci la lista
            savedChatList.innerHTML = '';
            
            // Se ci sono chat salvate, imposta il flag
            hasSavedChats = true;
            
            // Mostra il banner se richiesto e se ci sono chat salvate (e non è stato chiuso)
            if (checkForBanner && hasSavedChats) {
                const savedChatsBanner = document.getElementById('savedChatsBanner');
                if (savedChatsBanner && !sessionStorage.getItem('hideSavedChatsBanner')) {
                    setTimeout(() => {
                        savedChatsBanner.classList.add('visible');
                    }, 1500);
                }
            }
            
            // Aggiungi le chat salvate
            data.chats.forEach(chat => {
                const chatItem = document.createElement('div');
                chatItem.className = 'saved-chat-item';
                chatItem.dataset.chatId = chat.id;
                
                const date = new Date(chat.created_at);
                const formattedDate = date.toLocaleDateString('it-IT', { 
                    day: '2-digit', 
                    month: '2-digit', 
                    year: 'numeric',
                    hour: '2-digit',
                    minute: '2-digit'
                });
                
                chatItem.innerHTML = `
                    <h5>${chat.title || 'Chat senza titolo'}</h5>
                    <div class="saved-chat-date">${formattedDate}</div>
                    <div class="saved-chat-preview">${getPreview(chat.messages)}</div>
                    <div class="saved-chat-actions">
                        <button class="saved-chat-delete" data-chat-id="${chat.id}" title="Elimina">
                            <i class="fas fa-trash-alt"></i>
                        </button>
                    </div>
                `;
                
                savedChatList.appendChild(chatItem);
                
                // Aggiungi il listener per caricare la chat
                chatItem.addEventListener('click', function(e) {
                    // Ignora se si fa clic sul pulsante elimina
                    if (e.target.closest('.saved-chat-delete')) {
                        return;
                    }
                    
                    loadChat(chat.id);
                });
            });
            
            // Aggiungi i listener per eliminare le chat
            document.querySelectorAll('.saved-chat-delete').forEach(button => {
                button.addEventListener('click', function(e) {
                    e.stopPropagation();
                    const chatId = this.dataset.chatId;
                    deleteChat(chatId);
                });
            });
        } else {
            savedChatList.innerHTML = '<div class="no-saved-chats">Nessuna conversazione salvata</div>';
            hasSavedChats = false;
            
            // Nascondi il banner se non ci sono chat salvate
            const savedChatsBanner = document.getElementById('savedChatsBanner');
            if (savedChatsBanner) {
                savedChatsBanner.classList.remove('visible');
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
        const savedChatList = document.getElementById('savedChatList');
        savedChatList.innerHTML = '<div class="no-saved-chats">Errore nel caricamento delle conversazioni</div>';
        hasSavedChats = false;
    });
}

function loadChat(chatId) {
    fetch(`/api/chat/${chatId}`, {
        method: 'GET',
        headers: {
            'X-CSRFToken': config.csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.chat) {
            // Aggiorna l'ID della chat corrente
            currentChatId = chatId;
            
            // Pulisci la cronologia e la visualizzazione
            chatHistory = [];
            document.getElementById('chatMessages').innerHTML = '';
            
            // Carica i messaggi
            const messages = JSON.parse(data.chat.messages);
            messages.forEach(msg => {
                chatHistory.push(msg);
                addMessage(msg.content, msg.role === 'user' ? 'sent' : 'received');
            });
            
            // Aggiorna l'interfaccia
            isChatSaved = true;
            const chatSaveBtn = document.getElementById('chatSave');
            if (chatSaveBtn) chatSaveBtn.classList.add('saved');
            
            // Chiudi il pannello delle chat salvate
            const savedChatsPanel = document.getElementById('savedChatsPanel');
            if (savedChatsPanel) savedChatsPanel.classList.remove('visible');
            
            // Aggiorna localStorage
            saveChatToStorage();
            
            showTemporaryMessage("Conversazione caricata", "success");
        } else {
            showTemporaryMessage("Errore durante il caricamento della conversazione", "error");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showTemporaryMessage("Errore durante il caricamento della conversazione", "error");
    });
}

function deleteChat(chatId) {
    if (!confirm("Sei sicuro di voler eliminare questa conversazione?")) {
        return;
    }
    
    fetch(`/api/chat/${chatId}`, {
        method: 'DELETE',
        headers: {
            'X-CSRFToken': config.csrfToken
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Se stiamo visualizzando la chat che è stata eliminata, reimpostiamo tutto
            if (currentChatId === parseInt(chatId)) {
                // Resetta la chat corrente
                currentChatId = null;
                isChatSaved = false;
                const chatSaveBtn = document.getElementById('chatSave');
                if (chatSaveBtn) chatSaveBtn.classList.remove('saved');
                
                // Pulisci la cronologia e la visualizzazione
                chatHistory = [];
                document.getElementById('chatMessages').innerHTML = '';
                
                // Aggiungi un messaggio di benvenuto
                addMessage("Ciao! Sono l'assistente virtuale di Ristrutturazioni Morcianesi. Come posso aiutarti con il tuo preventivo?", 'received');
                
                // Aggiorna localStorage
                saveChatToStorage();
            }
            
            // Ricarica la lista delle chat
            loadSavedChats();
            
            showTemporaryMessage("Conversazione eliminata", "success");
        } else {
            showTemporaryMessage("Errore durante l'eliminazione della conversazione", "error");
        }
    })
    .catch(error => {
        console.error('Error:', error);
        showTemporaryMessage("Errore durante l'eliminazione della conversazione", "error");
    });
}

function toggleSavedChats() {
    const savedChatsPanel = document.getElementById('savedChatsPanel');
    savedChatsPanel.classList.toggle('visible');
    
    if (savedChatsPanel.classList.contains('visible')) {
        // Ricarica le chat quando si apre il pannello
        loadSavedChats();
    }
}

function getPreview(messagesJson) {
    try {
        const messages = typeof messagesJson === 'string' ? JSON.parse(messagesJson) : messagesJson;
        // Trova l'ultimo messaggio dell'assistente
        const lastAssistantMsg = [...messages].reverse().find(msg => msg.role === 'assistant');
        if (lastAssistantMsg) {
            return lastAssistantMsg.content.substring(0, 100) + (lastAssistantMsg.content.length > 100 ? '...' : '');
        }
        return "Nessuna risposta";
    } catch (error) {
        console.error('Errore nell\'elaborazione dell\'anteprima:', error);
        return "Anteprima non disponibile";
    }
}

// === FUNZIONI DI UTILITA' ===
function showSaveConfirmation() {
    const confirmation = document.getElementById('saveConfirmation');
    confirmation.classList.add('visible');
    
    setTimeout(() => {
        confirmation.classList.remove('visible');
    }, 3000);
}

function showTemporaryMessage(message, type = "info") {
    const confirmation = document.getElementById('saveConfirmation');
    if (confirmation) {
        confirmation.textContent = message;
        confirmation.className = `save-confirmation ${type} visible`;
        
        setTimeout(() => {
            confirmation.classList.remove('visible');
        }, 3000);
    }
}

// === INIZIALIZZAZIONE ===
function initializeChat() {
    // Carica la cronologia dalla localStorage all'avvio
    loadChatFromStorage();
    
    // Se l'utente è autenticato, sincronizza con le chat salvate nel database
    if (isLoggedIn) {
        setTimeout(() => {
            syncWithDatabase();
            loadSavedChats(true);
        }, 1000);
    }
    
    // Se è un popup, prova a recuperare la cronologia dalla finestra principale
    if (isPopup && window.opener.chatHistory) {
        try {
            chatHistory = [...window.opener.chatHistory];
            // Ricostruisce la chat precedente
            for (let msg of chatHistory) {
                addMessage(msg.content, msg.role === 'user' ? 'sent' : 'received');
            }
        } catch (error) {
            console.error('Errore nel recupero della cronologia:', error);
        }
    }
    
    // Aggiungiamo il messaggio di benvenuto solo se è la prima apertura
    if (document.getElementById('chatMessages').children.length === 0) {
        addMessage("Ciao! Sono l'assistente virtuale di Ristrutturazioni Morcianesi. Come posso aiutarti con il tuo preventivo?", 'received');
    }
    
    setupEventListeners();
}

function setupEventListeners() {
    // Event listeners base
    document.getElementById('chatSend').addEventListener('click', sendMessage);
    
    document.getElementById('chatInput').addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });
    
    // Event listeners per le funzioni di salvataggio chat
    if (isLoggedIn) {
        const chatSaveBtn = document.getElementById('chatSave');
        const chatSavedToggle = document.getElementById('chatSavedToggle');
        const savedChatsPanel = document.getElementById('savedChatsPanel');
        const savedChatsClose = document.getElementById('savedChatsClose');
        const savedChatsBanner = document.getElementById('savedChatsBanner');
        const viewSavedChatsBtn = document.getElementById('viewSavedChatsBtn');
        const closeBannerBtn = document.getElementById('closeBannerBtn');
        
        if (chatSaveBtn) {
            chatSaveBtn.addEventListener('click', saveChat);
        }
        
        if (chatSavedToggle) {
            chatSavedToggle.addEventListener('click', toggleSavedChats);
        }
        
        if (savedChatsClose) {
            savedChatsClose.addEventListener('click', () => {
                savedChatsPanel.classList.remove('visible');
            });
        }
        
        // Gestione del banner delle chat salvate
        if (viewSavedChatsBtn) {
            viewSavedChatsBtn.addEventListener('click', function() {
                toggleSavedChats();
                savedChatsBanner.classList.remove('visible');
                sessionStorage.setItem('hideSavedChatsBanner', 'true');
            });
        }
        
        if (closeBannerBtn) {
            closeBannerBtn.addEventListener('click', function() {
                savedChatsBanner.classList.remove('visible');
                sessionStorage.setItem('hideSavedChatsBanner', 'true');
            });
        }
    } else {
        const chatSaveLoginBtn = document.getElementById('chatSaveLogin');
        
        if (chatSaveLoginBtn) {
            chatSaveLoginBtn.addEventListener('click', () => {
                window.location.href = config.loginUrl;
            });
        }
    }
}

// Inizializza la chat quando il DOM è pronto
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializeChat);
} else {
    initializeChat();
}