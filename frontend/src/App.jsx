import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import ChatInterface from './components/ChatInterface';
import { api } from './api';
import './App.css';

function App() {
  const { conversationId } = useParams();
  const navigate = useNavigate();
  const [conversations, setConversations] = useState([]);
  const [currentConversationId, setCurrentConversationId] = useState(null);
  const [currentConversation, setCurrentConversation] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [isRegenerating, setIsRegenerating] = useState(false);
  const [isMobile, setIsMobile] = useState(window.innerWidth <= 768);
  const [showChat, setShowChat] = useState(false);
  const [errorMessage, setErrorMessage] = useState(null);

  useEffect(() => {
    const handleResize = () => {
      setIsMobile(window.innerWidth <= 768);
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Load conversations on mount
  useEffect(() => {
    loadConversations();
  }, []);

  // Sync URL param with state
  useEffect(() => {
    if (conversationId) {
      setCurrentConversationId(conversationId);
    }
  }, [conversationId]);

  // Load conversation details when selected
  useEffect(() => {
    if (currentConversationId) {
      loadConversation(currentConversationId);
    }
  }, [currentConversationId]);

  const loadConversations = async () => {
    try {
      const convs = await api.listConversations();
      setConversations(convs);
    } catch (error) {
      console.error('Failed to load conversations:', error);
      // Handle auth errors
      if (error.status === 401) {
        navigate('/');
      }
    }
  };

  const loadConversation = async (id) => {
    try {
      const conv = await api.getConversation(id);
      setCurrentConversation(conv);
      setErrorMessage(null);
    } catch (error) {
      console.error('Failed to load conversation:', error);

      // Handle different error types
      if (error.status === 401) {
        // Unauthenticated - redirect to landing page
        navigate('/');
      } else if (error.status === 403) {
        // Forbidden - access denied
        setErrorMessage('Access denied: You do not have permission to view this conversation');
        navigate('/chat');
        setCurrentConversationId(null);
        setCurrentConversation(null);
      } else if (error.status === 404) {
        // Not found
        setErrorMessage('Conversation not found');
        navigate('/chat');
        setCurrentConversationId(null);
        setCurrentConversation(null);
      } else {
        setErrorMessage('Failed to load conversation');
      }
    }
  };

  const handleNewConversation = async (type = 'council') => {
    try {
      const newConv = await api.createConversation(type);
      setConversations([
        { id: newConv.id, created_at: newConv.created_at, type: newConv.type, message_count: 0 },
        ...conversations,
      ]);
      // Navigate to new conversation URL
      navigate(`/chat/${newConv.id}`);
      if (isMobile) {
        setShowChat(true);
      }
    } catch (error) {
      console.error('Failed to create conversation:', error);
    }
  };

  const handleSelectConversation = (id) => {
    // Navigate to conversation URL (this will trigger useEffect to update state)
    navigate(`/chat/${id}`);
    if (isMobile) {
      setShowChat(true);
    }
  };

  const handleBackToList = () => {
    setShowChat(false);
  };

  const handleDeleteConversation = async (id) => {
    try {
      await api.deleteConversation(id);
      // Remove from local state
      setConversations((prev) => prev.filter((c) => c.id !== id));
      // If we deleted the current conversation, clear it
      if (currentConversationId === id) {
        setCurrentConversationId(null);
        setCurrentConversation(null);
      }
    } catch (error) {
      console.error('Failed to delete conversation:', error);
    }
  };

  const handleSendMessage = async (content, numTurns = 3, movieLength = 90) => {
    if (!currentConversationId || !currentConversation) return;

    const conversationType = currentConversation.type || 'council';

    if (conversationType === 'movie_script') {
      await handleMovieScriptMessage(content, numTurns, movieLength);
    } else {
      await handleCouncilMessage(content);
    }
  };

  const handleCouncilMessage = async (content) => {
    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message that will be updated progressively
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send message with streaming
      await api.sendMessageStream(currentConversationId, content, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage1 = event.data;
              lastMsg.loading.stage1 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage2_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage1 = false;
              lastMsg.loading.stage2 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage2_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.stage2 = event.data;
              lastMsg.metadata = event.metadata;
              lastMsg.loading.stage2 = false;
              return { ...prev, messages };
            });
            break;

          case 'stage3_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastMsg = messages[messages.length - 1];
              lastMsg.loading.stage2 = false;
              lastMsg.loading.stage3 = true;
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              messages[lastIdx] = {
                ...messages[lastIdx],
                stage3: event.data,
                loading: { ...messages[lastIdx].loading, stage3: false }
              };
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            // Reload conversations to get updated title
            loadConversations();
            break;

          case 'complete':
            // Stream complete, reload conversations list
            loadConversations();
            setIsLoading(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });
    } catch (error) {
      console.error('Failed to send message:', error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  const handleMovieScriptMessage = async (content, numTurns, movieLength) => {
    setIsLoading(true);
    try {
      // Optimistically add user message to UI
      const userMessage = { role: 'user', content };
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, userMessage],
      }));

      // Create a partial assistant message with 4 stages
      const assistantMessage = {
        role: 'assistant',
        stage1: null,
        stage2: null,
        stage3: null,
        stage4: null,
        metadata: null,
        loading: {
          stage1: false,
          stage2: false,
          stage3: false,
          stage4: false,
        },
      };

      // Add the partial assistant message
      setCurrentConversation((prev) => ({
        ...prev,
        messages: [...prev.messages, assistantMessage],
      }));

      // Send movie script request with streaming
      await api.sendMovieScriptStream(currentConversationId, content, numTurns, movieLength, (eventType, event) => {
        switch (eventType) {
          case 'stage1_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              messages[lastIdx] = {
                ...messages[lastIdx],
                loading: { ...messages[lastIdx].loading, stage1: true }
              };
              return { ...prev, messages };
            });
            break;

          case 'stage1_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              messages[lastIdx] = {
                ...messages[lastIdx],
                stage1: event.data,
                loading: { ...messages[lastIdx].loading, stage1: false }
              };
              return { ...prev, messages };
            });
            break;

          case 'stage2_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              messages[lastIdx] = {
                ...messages[lastIdx],
                loading: { ...messages[lastIdx].loading, stage1: false, stage2: true }
              };
              return { ...prev, messages };
            });
            break;

          case 'stage2_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              messages[lastIdx] = {
                ...messages[lastIdx],
                stage2: event.data,
                metadata: event.metadata,
                loading: { ...messages[lastIdx].loading, stage2: false }
              };
              return { ...prev, messages };
            });
            break;

          case 'stage3_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              messages[lastIdx] = {
                ...messages[lastIdx],
                loading: { ...messages[lastIdx].loading, stage2: false, stage3: true }
              };
              return { ...prev, messages };
            });
            break;

          case 'stage3_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              messages[lastIdx] = {
                ...messages[lastIdx],
                stage3: event.data,
                loading: { ...messages[lastIdx].loading, stage3: false }
              };
              return { ...prev, messages };
            });
            break;

          case 'stage4_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              messages[lastIdx] = {
                ...messages[lastIdx],
                loading: { ...messages[lastIdx].loading, stage3: false, stage4: true },
                stage4: {
                  dialogue_history: [],
                  collaborators: event.data?.collaborators || [],
                  num_turns: event.data?.num_turns || numTurns,
                }
              };
              return { ...prev, messages };
            });
            break;

          case 'stage4_turn':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              const lastMsg = messages[lastIdx];
              if (lastMsg.stage4) {
                messages[lastIdx] = {
                  ...lastMsg,
                  stage4: {
                    ...lastMsg.stage4,
                    dialogue_history: [
                      ...(lastMsg.stage4.dialogue_history || []),
                      event.data,
                    ]
                  }
                };
              }
              return { ...prev, messages };
            });
            break;

          case 'stage4_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              messages[lastIdx] = {
                ...messages[lastIdx],
                stage4: event.data,
                loading: { ...messages[lastIdx].loading, stage4: false }
              };
              return { ...prev, messages };
            });
            // Stage 4 is the last visible content - hide loading indicator
            setIsLoading(false);
            break;

          case 'validation_start':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              const lastMsg = messages[lastIdx];
              const newValidation = !lastMsg.validation
                ? { stage: event.stage, inProgress: true, results: [] }
                : { ...lastMsg.validation, stage: event.stage, inProgress: true };
              messages[lastIdx] = {
                ...lastMsg,
                validation: newValidation
              };
              return { ...prev, messages };
            });
            break;

          case 'validation_result':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              let lastMsg = { ...messages[lastIdx] };

              // Update validation results
              if (lastMsg.validation) {
                lastMsg.validation = {
                  ...lastMsg.validation,
                  results: [
                    ...(lastMsg.validation.results || []),
                    { model: event.model, compliance: event.compliance }
                  ]
                };
              }

              // Update stage1 with runtime validation info
              if (lastMsg.stage1 && event.model !== 'final_script') {
                lastMsg.stage1 = lastMsg.stage1.map(r =>
                  r.model === event.model
                    ? { ...r, runtime_validation: event.compliance }
                    : r
                );
              }

              // Update stage4 with runtime validation info
              if (lastMsg.stage4 && event.model === 'final_script') {
                lastMsg.stage4 = {
                  ...lastMsg.stage4,
                  runtime_validation: event.compliance
                };
              }

              messages[lastIdx] = lastMsg;
              return { ...prev, messages };
            });
            break;

          case 'validation_complete':
            setCurrentConversation((prev) => {
              const messages = [...prev.messages];
              const lastIdx = messages.length - 1;
              const lastMsg = messages[lastIdx];
              if (lastMsg.validation) {
                messages[lastIdx] = {
                  ...lastMsg,
                  validation: { ...lastMsg.validation, inProgress: false }
                };
              }
              return { ...prev, messages };
            });
            break;

          case 'title_complete':
            // Reload conversations to get updated title
            loadConversations();
            break;

          case 'complete':
            // Stream complete, reload conversations list
            loadConversations();
            setIsLoading(false);
            break;

          case 'error':
            console.error('Stream error:', event.message);
            setIsLoading(false);
            break;

          default:
            console.log('Unknown event type:', eventType);
        }
      });
    } catch (error) {
      console.error('Failed to send movie script message:', error);
      // Remove optimistic messages on error
      setCurrentConversation((prev) => ({
        ...prev,
        messages: prev.messages.slice(0, -2),
      }));
      setIsLoading(false);
    }
  };

  const handleRegenerateFinalScript = async () => {
    if (!currentConversationId) return;

    setIsRegenerating(true);
    try {
      const result = await api.regenerateFinalScript(currentConversationId);

      // Update the current conversation with the new refined script
      setCurrentConversation((prev) => {
        const messages = [...prev.messages];
        // Find the last assistant message with stage4
        for (let i = messages.length - 1; i >= 0; i--) {
          if (messages[i].role === 'assistant' && messages[i].stage4) {
            messages[i] = {
              ...messages[i],
              stage4: {
                ...messages[i].stage4,
                refined_script: result.refined_script,
              },
            };
            break;
          }
        }
        return { ...prev, messages };
      });
    } catch (error) {
      console.error('Failed to regenerate final script:', error);
      alert('Failed to regenerate final script: ' + error.message);
    } finally {
      setIsRegenerating(false);
    }
  };

  const showSidebar = !isMobile || !showChat;
  const showChatInterface = !isMobile || showChat;

  return (
    <div className={`app ${isMobile ? 'mobile' : ''}`}>
      {errorMessage && (
        <div className="error-banner" style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          backgroundColor: '#f44336',
          color: 'white',
          padding: '12px',
          textAlign: 'center',
          zIndex: 1000
        }}>
          {errorMessage}
          <button
            onClick={() => setErrorMessage(null)}
            style={{
              marginLeft: '12px',
              backgroundColor: 'transparent',
              border: '1px solid white',
              color: 'white',
              padding: '4px 8px',
              cursor: 'pointer',
              borderRadius: '4px'
            }}
          >
            Dismiss
          </button>
        </div>
      )}
      {showSidebar && (
        <Sidebar
          conversations={conversations}
          currentConversationId={currentConversationId}
          onSelectConversation={handleSelectConversation}
          onNewConversation={handleNewConversation}
          onDeleteConversation={handleDeleteConversation}
          isMobile={isMobile}
        />
      )}
      {showChatInterface && (
        <ChatInterface
          conversation={currentConversation}
          onSendMessage={handleSendMessage}
          isLoading={isLoading}
          isMobile={isMobile}
          onBack={handleBackToList}
          onRegenerateFinalScript={handleRegenerateFinalScript}
          isRegenerating={isRegenerating}
        />
      )}
    </div>
  );
}

export default App;
