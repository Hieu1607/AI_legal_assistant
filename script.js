document.addEventListener('DOMContentLoaded', () => {
    const userInput = document.getElementById('userInput');
    const sendButton = document.getElementById('sendButton');
    const chatBox = document.getElementById('chat-box');
    const welcomeScreen = document.getElementById('welcome-screen');

    const API_ENDPOINT = 'https://ai-legal-assistant-zswt.onrender.com/rag';

    let isFirstMessage = true; // Track if this is the first message

    const startChat = () => {
        // Hide welcome screen and show chat interface
        if (isFirstMessage && welcomeScreen) {
            welcomeScreen.style.animation = 'welcome-fade-out 0.5s ease-in forwards';
            setTimeout(() => {
                welcomeScreen.style.display = 'none';
                chatBox.classList.add('chat-started');
            }, 500)
            isFirstMessage = false;
        }
    };

    const disableInput = () => {
        userInput.disabled = true;
        sendButton.disabled = true;
        userInput.placeholder = 'Đang chờ phản hồi...';
        sendButton.style.opacity = '0.5';
        sendButton.style.cursor = 'not-allowed';
    };

    const enableInput = () => {
        userInput.disabled = false;
        sendButton.disabled = false;
        userInput.placeholder = 'Nhập câu hỏi của bạn...';
        sendButton.style.opacity = '1';
        sendButton.style.cursor = 'pointer';
        userInput.focus(); // Auto focus for convenience
    };

    const sendMessage = async () => {
        const question = userInput.value.trim();
        if (question === '') return;

        // Disable input and button while processing
        disableInput();

        // Start chat mode on first message
        startChat();

        displayMessage(question, 'user');
        userInput.value = '';
        userInput.style.height = 'auto'; // Reset height

        // Show typing indicator
        const typingElement = showTypingIndicator();

        try {
            const response = await fetch(API_ENDPOINT, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: question }),
            });

            if (!response.ok) {
                throw new Error(`API Error: ${response.statusText}`);
            }

            const result = await response.json();
            
            // Remove typing indicator
            removeTypingIndicator(typingElement);
            
            if (result.status === 'success' && result.data && result.data.answer) {
                const relevantChunks = result.data.relevant_chunks || [];
                await displayTypingMessage(result.data.answer, 'bot', relevantChunks);
            } else {
                await displayTypingMessage('Xin lỗi, tôi không thể tìm thấy câu trả lời.', 'bot');
            }

        } catch (error) {
            console.error('Failed to fetch from API:', error);
            // Remove typing indicator
            removeTypingIndicator(typingElement);
            await displayTypingMessage('Đã xảy ra lỗi khi kết nối với trợ lý. Vui lòng thử lại sau.', 'bot');
        } finally {
            // Re-enable input after response is complete
            enableInput();
        }
    };

    const displayMessage = (message, sender, relevantChunks = null) => {
        if (sender === 'bot' && relevantChunks && relevantChunks.length > 0) {
            // Create container for bot message with source button
            const messageContainer = document.createElement('div');
            messageContainer.classList.add('bot-message-container');
            
            // Create message element
            const messageElement = document.createElement('div');
            messageElement.classList.add('message', 'bot-message');
            messageElement.textContent = message;
            
            // Create source button
            const sourceButton = document.createElement('button');
            sourceButton.classList.add('source-button');
            sourceButton.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                </svg>
                Xem nguồn (${relevantChunks.length})
            `;
            
            // Add click event to source button
            sourceButton.addEventListener('click', () => {
                showSourceModal(relevantChunks);
            });
            
            messageContainer.appendChild(messageElement);
            messageContainer.appendChild(sourceButton);
            chatBox.appendChild(messageContainer);
        } else {
            // Regular message display
            const messageElement = document.createElement('div');
            messageElement.classList.add('message', `${sender}-message`);
            messageElement.textContent = message;
            chatBox.appendChild(messageElement);
        }
        chatBox.scrollTop = chatBox.scrollHeight; // Auto-scroll to the bottom
    };

    const showTypingIndicator = () => {
        const typingElement = document.createElement('div');
        typingElement.classList.add('message', 'bot-message', 'typing-indicator');
        typingElement.innerHTML = `
            <span class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </span>
            <span class="typing-text">AI đang suy nghĩ...</span>
        `;
        chatBox.appendChild(typingElement);
        chatBox.scrollTop = chatBox.scrollHeight;
        return typingElement;
    };

    const removeTypingIndicator = (typingElement) => {
        if (typingElement && typingElement.parentNode) {
            chatBox.removeChild(typingElement);
        }
    };

    const displayTypingMessage = async (message, sender, relevantChunks = null) => {
        if (sender === 'bot' && relevantChunks && relevantChunks.length > 0) {
            // Create container for bot message with source button
            const messageContainer = document.createElement('div');
            messageContainer.classList.add('bot-message-container');
            
            // Create message element
            const messageElement = document.createElement('div');
            messageElement.classList.add('message', 'bot-message');
            chatBox.appendChild(messageContainer);
            messageContainer.appendChild(messageElement);
            
            // Split message into words for more natural typing effect
            const words = message.split(' ');
            let currentText = '';
            
            for (let i = 0; i < words.length; i++) {
                currentText += (i > 0 ? ' ' : '') + words[i];
                messageElement.textContent = currentText;
                chatBox.scrollTop = chatBox.scrollHeight;
                
                // Add delay between words (adjust speed here)
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            
            // Add a cursor effect at the end
            messageElement.innerHTML = currentText + '<span class="typing-cursor">|</span>';
            
            // Remove cursor after a short delay and add source button
            setTimeout(() => {
                messageElement.textContent = currentText;
                
                // Create and add source button
                const sourceButton = document.createElement('button');
                sourceButton.classList.add('source-button');
                sourceButton.innerHTML = `
                    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor">
                        <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                    </svg>
                    Xem nguồn (${relevantChunks.length})
                `;
                
                // Add click event to source button
                sourceButton.addEventListener('click', () => {
                    showSourceModal(relevantChunks);
                });
                
                messageContainer.appendChild(sourceButton);
            }, 1000);
        } else {
            // Regular typing message display
            const messageElement = document.createElement('div');
            messageElement.classList.add('message', `${sender}-message`);
            chatBox.appendChild(messageElement);
            
            // Split message into words for more natural typing effect
            const words = message.split(' ');
            let currentText = '';
            
            for (let i = 0; i < words.length; i++) {
                currentText += (i > 0 ? ' ' : '') + words[i];
                messageElement.textContent = currentText;
                chatBox.scrollTop = chatBox.scrollHeight;
                
                // Add delay between words (adjust speed here)
                await new Promise(resolve => setTimeout(resolve, 50));
            }
            
            // Add a cursor effect at the end
            messageElement.innerHTML = currentText + '<span class="typing-cursor">|</span>';
            
            // Remove cursor after a short delay
            setTimeout(() => {
                messageElement.textContent = currentText;
            }, 1000);
        }
    };

    sendButton.addEventListener('click', sendMessage);
    userInput.addEventListener('keydown', (event) => {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendMessage();
        }
    });

    // Handle suggestion clicks
    document.addEventListener('click', (event) => {
        if (event.target.classList.contains('suggestion-item')) {
            // Don't process if input is disabled (bot is responding)
            if (userInput.disabled) return;
            
            const suggestionText = event.target.textContent.trim();
            userInput.value = `${suggestionText.toLowerCase()}`;
            sendMessage();
        }
    });

    // Auto-resize textarea
    userInput.addEventListener('input', () => {
        userInput.style.height = 'auto';
        userInput.style.height = `${userInput.scrollHeight}px`;
    });

    // Source modal functions
    const showSourceModal = (relevantChunks) => {
        // Create modal overlay if it doesn't exist
        let modalOverlay = document.getElementById('source-modal');
        if (!modalOverlay) {
            modalOverlay = document.createElement('div');
            modalOverlay.id = 'source-modal';
            modalOverlay.classList.add('modal-overlay');
            document.body.appendChild(modalOverlay);
        }

        // Create modal content
        modalOverlay.innerHTML = `
            <div class="modal-content">
                <div class="modal-header">
                    <h3>Nguồn thông tin liên quan (${relevantChunks.length} đoạn)</h3>
                    <button class="modal-close">&times;</button>
                </div>
                <div class="modal-body">
                    ${relevantChunks.map((chunk, index) => `
                        <div class="chunk-item">
                            <div class="chunk-header">
                                <div class="chunk-source">${chunk.title || 'Không xác định'}</div>
                                <div class="chunk-number">Đoạn ${index + 1}</div>
                            </div>
                            <div class="chunk-content">${chunk.text || ''}</div>
                            <div class="chunk-info">
                                ${chunk.date_of_issue ? `<span class="chunk-date">Ngày ban hành: ${chunk.date_of_issue}</span>` : ''}
                                ${chunk.update_day ? `<span class="chunk-update">Cập nhật: ${chunk.update_day}</span>` : ''}
                                ${chunk.chunk_id ? `<span class="chunk-id">ID: ${chunk.chunk_id}</span>` : ''}
                            </div>
                        </div>
                    `).join('')}
                </div>
            </div>
        `;

        // Show modal
        setTimeout(() => {
            modalOverlay.classList.add('show');
        }, 10);

        // Add close event listeners
        const closeBtn = modalOverlay.querySelector('.modal-close');
        closeBtn.addEventListener('click', hideSourceModal);
        
        modalOverlay.addEventListener('click', (e) => {
            if (e.target === modalOverlay) {
                hideSourceModal();
            }
        });

        // Add keyboard event listener
        document.addEventListener('keydown', handleModalKeydown);
    };

    const hideSourceModal = () => {
        const modalOverlay = document.getElementById('source-modal');
        if (modalOverlay) {
            modalOverlay.classList.remove('show');
            setTimeout(() => {
                modalOverlay.remove();
            }, 300);
        }
        document.removeEventListener('keydown', handleModalKeydown);
    };

    const handleModalKeydown = (e) => {
        if (e.key === 'Escape') {
            hideSourceModal();
        }
    };
});