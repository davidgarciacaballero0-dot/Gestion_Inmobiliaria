import { useState, useEffect, useRef, useCallback } from 'react';
import {
  Mic, MicOff, Send, Volume2, VolumeX, Sparkles, X, MessageSquare,
  Calendar, Check, AlertCircle, Bot
} from 'lucide-react';
import guiaVirtualService from '../services/guiaVirtualService';
import './GuiaVirtualVoz.css';

/**
 * GuiaVirtualVoz — Asistente de voz con IA espacial para recorridos 3D.
 *
 * @param {object} props
 * @param {number} props.inmuebleId - ID de la propiedad
 * @param {string} props.habitacionActiva - Nombre de la escena o habitación actual
 * @param {Function} [props.onAgendarCita] - Callback para abrir modal de agendamiento
 */
const GuiaVirtualVoz = ({ inmuebleId, habitacionActiva = 'Recorrido General', onAgendarCita }) => {
  const [isOpen, setIsOpen] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [audioMuted, setAudioMuted] = useState(false);
  const [inputText, setInputText] = useState('');
  const [cargando, setCargando] = useState(false);
  const [mensajes, setMensajes] = useState([
    {
      id: 1,
      sender: 'assistant',
      text: '¡Hola! Soy Sofía, tu guía virtual con IA. Navega por las habitaciones o pregúntame lo que desees por voz o texto.',
    },
  ]);

  const messagesEndRef = useRef(null);
  const recognitionRef = useRef(null);
  const audioPlayerRef = useRef(null);
  const prevHabitacionRef = useRef('');

  // ─── Scroll automático al final de mensajes ───
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [mensajes]);

  // ─── Síntesis de Voz (TTS) ───
  const hablarTexto = useCallback((texto, audioBase64 = null) => {
    if (audioMuted) return;

    // Detener cualquier audio o síntesis previa
    if (window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    if (audioPlayerRef.current) {
      audioPlayerRef.current.pause();
      audioPlayerRef.current = null;
    }

    // 1. Si el servidor envió audio MP3 (ElevenLabs)
    if (audioBase64) {
      const audio = new Audio(audioBase64);
      audioPlayerRef.current = audio;
      setIsSpeaking(true);
      audio.onended = () => setIsSpeaking(false);
      audio.onerror = () => setIsSpeaking(false);
      audio.play().catch(() => setIsSpeaking(false));
      return;
    }

    // 2. Fallback: Web Speech Synthesis API nativa
    if ('speechSynthesis' in window) {
      const utterance = new SpeechSynthesisUtterance(texto);
      utterance.lang = 'es-ES';
      utterance.rate = 1.05;
      utterance.pitch = 1.02;

      // Buscar voz en español si está disponible
      const voices = window.speechSynthesis.getVoices();
      const spanishVoice = voices.find((v) => v.lang.startsWith('es') && (v.name.includes('Google') || v.name.includes('Natural') || v.name.includes('Sabina') || v.name.includes('Helena') || v.name.includes('Mónica')));
      if (spanishVoice) {
        utterance.voice = spanishVoice;
      }

      utterance.onstart = () => setIsSpeaking(true);
      utterance.onend = () => setIsSpeaking(false);
      utterance.onerror = () => setIsSpeaking(false);

      window.speechSynthesis.speak(utterance);
    }
  }, [audioMuted]);

  // ─── Narración Espacial Automática al Cambiar de Habitación ───
  useEffect(() => {
    if (!habitacionActiva || habitacionActiva === prevHabitacionRef.current || !inmuebleId) {
      return;
    }
    prevHabitacionRef.current = habitacionActiva;

    // Solicitar narración espacial a la IA
    const obtenerNarracion = async () => {
      try {
        const data = await guiaVirtualService.narrar(inmuebleId, habitacionActiva);
        if (data && data.narracion) {
          setMensajes((prev) => [
            ...prev,
            {
              id: Date.now(),
              sender: 'assistant',
              text: data.narracion,
              habitacion: habitacionActiva,
            },
          ]);
          hablarTexto(data.narracion, data.audio_base64);
        }
      } catch (err) {
        console.error('Error al obtener narración espacial:', err);
      }
    };

    obtenerNarracion();
  }, [habitacionActiva, inmuebleId, hablarTexto]);

  // ─── Reconocimiento de Voz (STT) ───
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'es-BO';

      recognition.onresult = (event) => {
        const transcript = event.results[0][0].transcript;
        setIsRecording(false);
        if (transcript) {
          handleEnviarConsulta(transcript);
        }
      };

      recognition.onerror = (event) => {
        console.warn('Error en reconocimiento de voz:', event.error);
        setIsRecording(false);
      };

      recognition.onend = () => {
        setIsRecording(false);
      };

      recognitionRef.current = recognition;
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const toggleGrabacion = () => {
    if (!recognitionRef.current) {
      alert('Tu navegador no soporta reconocimiento de voz nativo. Por favor escribe tu mensaje.');
      return;
    }

    if (isRecording) {
      recognitionRef.current.stop();
      setIsRecording(false);
    } else {
      try {
        recognitionRef.current.start();
        setIsRecording(true);
      } catch (err) {
        console.error('Error iniciando micrófono:', err);
      }
    }
  };

  // ─── Enviar Consulta / Pregunta a la IA ───
  const handleEnviarConsulta = async (textoAEnviar = null) => {
    const query = (textoAEnviar || inputText).trim();
    if (!query || cargando) return;

    setInputText('');
    const userMsgId = Date.now();
    setMensajes((prev) => [
      ...prev,
      { id: userMsgId, sender: 'user', text: query },
    ]);

    setCargando(true);
    try {
      const resp = await guiaVirtualService.consultar(inmuebleId, query, habitacionActiva);
      const respuestaTexto = resp?.respuesta || 'Disculpa, no pude procesar la consulta en este momento.';

      setMensajes((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          text: respuestaTexto,
          intencion: resp?.intencion,
          datosAgendamiento: resp?.datos_agendamiento,
        },
      ]);

      hablarTexto(respuestaTexto, resp?.audio_base64);

      // Si la IA detecta intención de agendar cita y existe el callback
      if (resp?.intencion === 'agendar_visita' && onAgendarCita) {
        setTimeout(() => {
          onAgendarCita();
        }, 1500);
      }
    } catch (err) {
      console.error('Error consultando a la guía:', err);
      setMensajes((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'assistant',
          text: 'Hubo un inconveniente conectando con el servicio de IA. ¿Deseas intentar de nuevo?',
        },
      ]);
    } finally {
      setCargando(false);
    }
  };

  const sugerenciasRapidas = [
    '¿Cuánto cuesta el alquiler?',
    '¿Qué comodidades incluye?',
    '¿Tiene garaje o parqueo?',
    'Quiero agendar una visita presencial',
  ];

  return (
    <div className="guia-virtual-container">
      {/* Ventana Modal Desplegable */}
      {isOpen && (
        <div className="guia-card">
          {/* Header */}
          <div className="guia-header">
            <div className="guia-header-info">
              <div className={`guia-avatar-pulse ${isSpeaking ? 'speaking' : ''}`}>
                <Bot size={16} />
              </div>
              <div>
                <h4 className="guia-header-title">
                  Guía Virtual Sofía
                  <Sparkles size={14} color="#f59e0b" />
                </h4>
                <span className="guia-header-badge">En vivo: {habitacionActiva}</span>
              </div>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <button
                className="guia-close-btn"
                onClick={() => {
                  setAudioMuted(!audioMuted);
                  if (window.speechSynthesis) window.speechSynthesis.cancel();
                }}
                title={audioMuted ? 'Activar voz' : 'Silenciar voz'}
              >
                {audioMuted ? <VolumeX size={16} /> : <Volume2 size={16} />}
              </button>
              <button
                className="guia-close-btn"
                onClick={() => setIsOpen(false)}
                title="Minimizar guía"
              >
                <X size={16} />
              </button>
            </div>
          </div>

          {/* Body / Mensajes */}
          <div className="guia-body">
            {mensajes.map((msg) => (
              <div key={msg.id} className={`guia-bubble ${msg.sender}`}>
                {msg.text}
                {msg.sender === 'assistant' && isSpeaking && msg.id === mensajes[mensajes.length - 1]?.id && (
                  <div className="guia-wave-container">
                    <div className="guia-wave-bar" />
                    <div className="guia-wave-bar" />
                    <div className="guia-wave-bar" />
                    <div className="guia-wave-bar" />
                    <div className="guia-wave-bar" />
                  </div>
                )}
              </div>
            ))}
            {cargando && (
              <div className="guia-bubble assistant" style={{ fontStyle: 'italic', opacity: 0.8 }}>
                Sofía está analizando la propiedad...
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Pills de Sugerencias */}
          <div className="guia-sugerencias">
            {sugerenciasRapidas.map((sug, idx) => (
              <button
                key={idx}
                className="guia-pill-btn"
                onClick={() => handleEnviarConsulta(sug)}
              >
                {sug}
              </button>
            ))}
          </div>

          {/* Footer / Input */}
          <div className="guia-footer">
            <input
              type="text"
              className="guia-input"
              placeholder="Pregúntale a Sofía o habla..."
              value={inputText}
              onChange={(e) => setInputText(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleEnviarConsulta()}
            />
            <button
              className={`guia-mic-btn ${isRecording ? 'recording' : ''}`}
              onClick={toggleGrabacion}
              title={isRecording ? 'Detener micrófono' : 'Hablar por micrófono'}
            >
              {isRecording ? <MicOff size={18} /> : <Mic size={18} />}
            </button>
            <button
              className="guia-send-btn"
              onClick={() => handleEnviarConsulta()}
              disabled={!inputText.trim() || cargando}
              title="Enviar consulta"
            >
              <Send size={16} />
            </button>
          </div>
        </div>
      )}

      {/* Botón Trigger Flotante */}
      {!isOpen && (
        <button className="guia-trigger-btn" onClick={() => setIsOpen(true)}>
          <div className={`guia-avatar-pulse ${isSpeaking ? 'speaking' : ''}`}>
            <Bot size={18} />
          </div>
          <span>Guía Virtual con Voz</span>
          <Sparkles size={16} color="#fbbf24" />
        </button>
      )}
    </div>
  );
};

export default GuiaVirtualVoz;
