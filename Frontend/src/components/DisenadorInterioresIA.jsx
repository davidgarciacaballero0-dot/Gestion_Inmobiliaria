import React, { useState, useEffect, useRef, useMemo } from 'react';
import { Sparkles, Mic, MicOff, Wand2, RefreshCw, UploadCloud, Image as ImageIcon, Check, Plus, Trash2, Palette, Lamp, Sofa, Lightbulb, AlertCircle, CheckCircle2, Home, Tag, ChevronDown, CheckCheck } from 'lucide-react';
import stagingService from '../services/stagingService';
import AntesDespuesSlider from './AntesDespuesSlider';
import './DisenadorInterioresIA.css';


/**
 * Componente interactivo para diseño de interiores y amoblado virtual
 */
const DisenadorInterioresIA = ({
  inmuebleId,
  inmuebleTitulo = 'Inmueble',
  inmueble = null,
  multimedia: multimediaProp = [],
  imagenOriginal,
  amobladosIniciales = [],
  esPropietario = false,
  onAmobladoGenerado,
}) => {
  // Lista de multimedia local para permitir actualizaciones reactivas (ej. al clasificar foto)
  const [listaMultimedia, setListaMultimedia] = useState(
    (inmueble?.multimedia && inmueble.multimedia.length > 0) ? inmueble.multimedia : multimediaProp
  );

  useEffect(() => {
    const mediaActual = (inmueble?.multimedia && inmueble.multimedia.length > 0) ? inmueble.multimedia : multimediaProp;
    setListaMultimedia(mediaActual || []);
  }, [inmueble, multimediaProp]);

  // ─── Generador Dinámico de Ambientes Reales del Inmueble ───────────────────
  const ambientesReales = useMemo(() => {
    const list = [
      { id: 'sala', label: 'Sala / Comedor', placeholder: 'Ej: Sala moderna con sofá seccional en lino gris...' },
      { id: 'cocina', label: 'Cocina', placeholder: 'Ej: Cocina minimalista con isla central y encimeras de cuarzo blanco...' },
    ];

    const cantHabitaciones = Number(inmueble?.habitaciones || 0);
    if (cantHabitaciones === 1) {
      list.push({ id: 'dormitorio-principal', label: 'Dormitorio Principal', placeholder: 'Ej: Cama King con cabecera acolchada, mesas flotantes y luces cálidas...' });
    } else if (cantHabitaciones > 1) {
      for (let i = 1; i <= cantHabitaciones; i++) {
        list.push({
          id: `dormitorio-${i}`,
          label: `Dormitorio ${i}`,
          placeholder: `Ej: Dormitorio ${i} estilo ejecutivo con cama king size...`
        });
      }
    }

    const cantBanos = Number(inmueble?.banos || 0);
    if (cantBanos === 1) {
      list.push({ id: 'bano-principal', label: 'Baño Principal', placeholder: 'Ej: Baño spa con espejo retroiluminado, grifería moderna y revestimiento cerámico...' });
    } else if (cantBanos > 1) {
      for (let i = 1; i <= cantBanos; i++) {
        list.push({
          id: `bano-${i}`,
          label: `Baño ${i}`,
          placeholder: `Ej: Baño ${i} contemporáneo con revestimiento en mármol...`
        });
      }
    }

    if (inmueble?.garaje) {
      list.push({ id: 'garaje', label: 'Garaje / Parqueo', placeholder: 'Ej: Garaje amplio con iluminación LED perimetral...' });
    }

    // Agregar ambientes personalizados detectados en fotos subidas por el propietario
    const fotos2D = (listaMultimedia || []).filter(m => m.tipo === 'imagen' || !m.tipo);
    fotos2D.forEach(f => {
      const desc = (f.descripcion || '').trim();
      if (desc && !list.some(a => a.label.toLowerCase() === desc.toLowerCase())) {
        list.push({
          id: desc.toLowerCase().replace(/\s+/g, '-'),
          label: desc,
          icon: '🏠',
          placeholder: `Ej: Diseño y amoblado personalizado para ${desc}...`
        });
      }
    });

    // Pestaña General / Sin clasificar (para fotos que no tienen etiqueta explícita de habitación)
    list.push({
      id: 'sin-clasificar',
      label: 'General / Sin clasificar',
      icon: '📁',
      placeholder: 'Ej: Propuesta de diseño para espacio del inmueble...'
    });

    // Si es cliente/visitante, solo mostrar ambientes que TIENEN al menos una foto disponible
    if (!esPropietario) {
      return list.filter(amb => {
        if (amb.id === 'sin-clasificar') {
          return fotos2D.some(f => !f.descripcion || f.descripcion.trim() === '');
        }
        return fotos2D.some(f => (f.descripcion || '').toLowerCase().includes(amb.label.toLowerCase()) || (f.descripcion || '').toLowerCase() === amb.id);
      });
    }

    return list;
  }, [inmueble, listaMultimedia, esPropietario]);

  // ─── Estados de Interacción ───────────────────────────────────────────────
  const [ambienteActivo, setAmbienteActivo] = useState(ambientesReales[0]?.id || 'sala');
  const [estiloSeleccionado, setEstiloSeleccionado] = useState('moderno');
  const [promptTexto, setPromptTexto] = useState('');
  const [cargando, setCargando] = useState(false);
  const [amoblados, setAmoblados] = useState(amobladosIniciales);
  const [amobladoActual, setAmobladoActual] = useState(null);
  const [mensajeExito, setMensajeExito] = useState('');
  const [mensajeError, setMensajeError] = useState('');

  // ─── Foto Seleccionada y Subida ───────────────────────────────────────────
  const [fotoSeleccionadaId, setFotoSeleccionadaId] = useState(null);
  const [archivoNuevo, setArchivoNuevo] = useState(null);
  const [previewNuevo, setPreviewNuevo] = useState(null);
  const [guardarEnInmueble, setGuardarEnInmueble] = useState(false);
  const [modalClasificarFoto, setModalClasificarFoto] = useState(null);
  const fileInputRef = useRef(null);

  // ─── Estado del Reconocimiento de Voz ─────────────────────────────────────
  const [escuchandoVoz, setEscuchandoVoz] = useState(false);
  const [soportaVoz, setSoportaVoz] = useState(true);
  const recognitionRef = useRef(null);

  // Filtrar fotos 2D del inmueble
  const todasFotos2D = (listaMultimedia || []).filter(m => m.tipo === 'imagen' || !m.tipo);

  // Filtrar fotos según el ambiente activo
  const fotosAmbienteActivo = useMemo(() => {
    if (ambienteActivo === 'sin-clasificar') {
      return todasFotos2D.filter(f => !f.descripcion || f.descripcion.trim() === '' || f.descripcion.toLowerCase() === 'general');
    }
    const ambObj = ambientesReales.find(a => a.id === ambienteActivo);
    if (!ambObj) return todasFotos2D;

    const labelLower = ambObj.label.toLowerCase();
    const idLower = ambObj.id.toLowerCase();

    return todasFotos2D.filter(f => {
      const desc = (f.descripcion || '').toLowerCase();
      return desc === labelLower || desc.includes(labelLower) || desc === idLower;
    });
  }, [todasFotos2D, ambienteActivo, ambientesReales]);

  // Foto original a mostrar en el comparador
  const fotoOriginalEfectiva = previewNuevo ||
    (fotoSeleccionadaId ? todasFotos2D.find(f => f.id === fotoSeleccionadaId)?.archivo : null) ||
    fotosAmbienteActivo[0]?.archivo ||
    todasFotos2D[0]?.archivo ||
    imagenOriginal ||
    'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=80';

  useEffect(() => {
    setAmoblados(amobladosIniciales);
    if (amobladosIniciales.length > 0) {
      setAmobladoActual(amobladosIniciales[amobladosIniciales.length - 1]);
    }
  }, [amobladosIniciales]);

  // Asegurar que si el ambiente activo no existe, seleccione el primero
  useEffect(() => {
    if (ambientesReales.length > 0 && !ambientesReales.some(a => a.id === ambienteActivo)) {
      setAmbienteActivo(ambientesReales[0].id);
    }
  }, [ambientesReales, ambienteActivo]);

  // Inicializar Web Speech API
  useEffect(() => {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'es-ES';

      recognition.onstart = () => {
        setEscuchandoVoz(true);
        setMensajeError('');
      };

      recognition.onresult = (event) => {
        const textoDetectado = event.results[0][0].transcript;
        if (textoDetectado) {
          setPromptTexto(prev => (prev ? `${prev} ${textoDetectado}` : textoDetectado));
        }
      };

      recognition.onerror = (event) => {
        console.warn('[SpeechRecognition error]:', event.error);
        setEscuchandoVoz(false);
        if (event.error === 'not-allowed') {
          setMensajeError('Permiso de micrófono denegado en tu navegador.');
        }
      };

      recognition.onend = () => {
        setEscuchandoVoz(false);
      };

      recognitionRef.current = recognition;
    } else {
      setSoportaVoz(false);
    }

    return () => {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.stop();
        } catch (e) {
          // ignore
        }
      }
    };
  }, []);

  const toggleGrabacionVoz = () => {
    if (!recognitionRef.current) {
      setMensajeError('El reconocimiento de voz no está disponible en este navegador.');
      return;
    }

    if (escuchandoVoz) {
      recognitionRef.current.stop();
      setEscuchandoVoz(false);
    } else {
      try {
        setMensajeError('');
        recognitionRef.current.start();
      } catch (err) {
        console.error('Error al iniciar micrófono:', err);
      }
    }
  };

  const handleSeleccionarArchivo = (e) => {
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.type.startsWith('image/')) {
      setMensajeError('Por favor selecciona un archivo de imagen válido (JPG, PNG o WebP).');
      return;
    }

    setArchivoNuevo(file);
    setPreviewNuevo(URL.createObjectURL(file));
    setFotoSeleccionadaId(null);
    setMensajeError('');
  };

  const handleRemoverArchivoNuevo = () => {
    setArchivoNuevo(null);
    if (previewNuevo) {
      URL.revokeObjectURL(previewNuevo);
      setPreviewNuevo(null);
    }
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleAsignarAmbienteAFoto = async (fotoId, nuevoAmbienteLabel) => {
    try {
      await stagingService.asignarAmbiente(fotoId, nuevoAmbienteLabel);
      setListaMultimedia(prev =>
        prev.map(f => (f.id === fotoId ? { ...f, descripcion: nuevoAmbienteLabel } : f))
      );
      setModalClasificarFoto(null);
      setMensajeExito(`Fotografía asignada exitosamente a "${nuevoAmbienteLabel}".`);
    } catch (err) {
      console.error('Error al asignar ambiente:', err);
      setMensajeError('No se pudo actualizar el ambiente de la fotografía.');
    }
  };

  const aplicarSugerencia = (sugerencia) => {
    setEstiloSeleccionado(sugerencia.id);
    setPromptTexto(sugerencia.prompt);
  };

  const handleGenerarAmoblado = async (e) => {
    if (e) e.preventDefault();
    if (!inmuebleId) return;

    setCargando(true);
    setMensajeExito('');
    setMensajeError('');

    try {
      const ambActualObj = ambientesReales.find(a => a.id === ambienteActivo) || ambientesReales[0];
      const res = await stagingService.generarAmoblado({
        inmueble_id: inmuebleId,
        multimedia_id: archivoNuevo ? null : (fotoSeleccionadaId || fotosAmbienteActivo[0]?.id || undefined),
        estilo: estiloSeleccionado,
        ambiente: ambActualObj?.label || 'Sala / Comedor',
        prompt: promptTexto.trim() || undefined,
        tipo: 'foto_2d',
        imagen: archivoNuevo || undefined,
        guardar_en_inmueble: esPropietario && guardarEnInmueble,
      });

      const nuevoAmoblado = res?.data || res;
      setAmobladoActual(nuevoAmoblado);
      setAmoblados(prev => {
        const filtrados = (prev || []).filter(a => a.id !== nuevoAmoblado.id);
        return [...filtrados, nuevoAmoblado];
      });

      setMensajeExito(`¡Propuesta de amoblado para ${ambActualObj?.label} generada exitosamente!`);
      if (onAmobladoGenerado) {
        onAmobladoGenerado(nuevoAmoblado);
      }
    } catch (err) {
      console.error('Error al amoblar con IA:', err);
      setMensajeError(err.response?.data?.error || 'No se pudo generar el amoblado virtual. Inténtalo nuevamente.');
    } finally {
      setCargando(false);
    }
  };

  const ambienteObj = ambientesReales.find(a => a.id === ambienteActivo) || ambientesReales[0] || { label: 'Ambiente', placeholder: '' };
  const detalleDiseno = amobladoActual?.detalle_diseno || null;

  return (
    <div className="disenador-ia-container">
      {/* ─── Encabezado Formal ────────────────────────────────────────────── */}
      <div className="disenador-ia-header">
        <h3 className="disenador-ia-title">Amoblado Virtual y Diseño de Interiores</h3>
        <p className="disenador-ia-subtitle">
          {esPropietario
            ? `Administra, sube fotografías y genera propuestas de remodelación fotorrealistas para cada espacio real de ${inmuebleTitulo}.`
            : `Explora el potencial de los ambientes reales de ${inmuebleTitulo} visualizando opciones de amoblado y estilos decorativos.`}
        </p>
      </div>

      {/* ─── 1. Selector de Ambientes Reales del Inmueble ─────────────────── */}
      <div className="disenador-ia-section">
        <div className="disenador-ia-section-title">
          <Home size={16} />
          <span>1. Habitaciones y ambientes reales del inmueble:</span>
        </div>

        {ambientesReales.length === 0 ? (
          <div className="disenador-ia-empty-rooms">
            <span>Este inmueble aún no tiene fotografías de ambientes publicadas.</span>
          </div>
        ) : (
          <div className="disenador-ia-ambientes-grid">
            {ambientesReales.map((amb) => {
              const isActivo = ambienteActivo === amb.id;
              // Contar fotos para este ambiente
              const count = amb.id === 'sin-clasificar'
                ? todasFotos2D.filter(f => !f.descripcion || f.descripcion.trim() === '').length
                : todasFotos2D.filter(f => (f.descripcion || '').toLowerCase().includes(amb.label.toLowerCase())).length;

              return (
                <button
                  key={amb.id}
                  type="button"
                  className={`disenador-ia-ambiente-btn ${isActivo ? 'active' : ''}`}
                  onClick={() => {
                    setAmbienteActivo(amb.id);
                    setArchivoNuevo(null);
                    setPreviewNuevo(null);
                    setFotoSeleccionadaId(null);
                  }}
                >
                  <span className="disenador-ia-ambiente-label">{amb.label}</span>
                  {count > 0 && <span className="disenador-ia-ambiente-count">{count}</span>}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* ─── 2. Galería de Fotos del Ambiente Activo ──────────────────────── */}
      <div className="disenador-ia-section">
        <div className="disenador-ia-section-title">
          <ImageIcon size={16} />
          <span>2. Fotografía del espacio ({ambienteObj.label}):</span>
        </div>

        <div className="disenador-ia-fotos-container">
          {/* Opción de Subir Nueva Foto: SOLO PARA PROPIETARIOS */}
          {esPropietario && (
            <div className="disenador-ia-upload-card">
              <input
                type="file"
                ref={fileInputRef}
                accept="image/*"
                style={{ display: 'none' }}
                onChange={handleSeleccionarArchivo}
              />
              {previewNuevo ? (
                <div className="disenador-ia-uploaded-preview">
                  <img src={previewNuevo} alt="Nueva foto" />
                  <div className="disenador-ia-uploaded-tag">
                    <Check size={12} /> Nueva foto
                  </div>
                  <button
                    type="button"
                    className="disenador-ia-remove-upload-btn"
                    onClick={handleRemoverArchivoNuevo}
                    title="Eliminar foto seleccionada"
                  >
                    <Trash2 size={13} />
                  </button>
                </div>
              ) : (
                <button
                  type="button"
                  className="disenador-ia-upload-btn"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <UploadCloud size={22} />
                  <span>Subir foto de {ambienteObj.label}</span>
                  <small>JPG, PNG o WebP</small>
                </button>
              )}
            </div>
          )}

          {/* Fotos del Ambiente Activo */}
          {fotosAmbienteActivo.map((foto, idx) => {
            const isSelected = !previewNuevo && (fotoSeleccionadaId === foto.id || (!fotoSeleccionadaId && idx === 0));
            return (
              <div
                key={foto.id || idx}
                className={`disenador-ia-foto-item ${isSelected ? 'selected' : ''}`}
                onClick={() => {
                  handleRemoverArchivoNuevo();
                  setFotoSeleccionadaId(foto.id);
                }}
              >
                <img src={foto.archivo} alt={foto.descripcion || `Foto ${idx + 1}`} />
                {isSelected && (
                  <div className="disenador-ia-foto-check">
                    <Check size={14} />
                  </div>
                )}
                {foto.descripcion ? (
                  <span className="disenador-ia-foto-tag">{foto.descripcion}</span>
                ) : (
                  <span className="disenador-ia-foto-tag sin-tag">Sin clasificar</span>
                )}

                {/* Botón de Clasificación Rápida para Propietarios */}
                {esPropietario && (
                  <button
                    type="button"
                    className="disenador-ia-tag-btn"
                    onClick={(e) => {
                      e.stopPropagation();
                      setModalClasificarFoto(modalClasificarFoto === foto.id ? null : foto.id);
                    }}
                    title="Clasificar habitación"
                  >
                    <Tag size={12} />
                  </button>
                )}

                {/* Menú flotante de clasificación */}
                {modalClasificarFoto === foto.id && (
                  <div className="disenador-ia-tag-menu" onClick={(e) => e.stopPropagation()}>
                    <span className="disenador-ia-tag-menu-title">Asignar a ambiente:</span>
                    {ambientesReales
                      .filter(a => a.id !== 'sin-clasificar')
                      .map(a => (
                        <button
                          key={a.id}
                          type="button"
                          className="disenador-ia-tag-menu-item"
                          onClick={() => handleAsignarAmbienteAFoto(foto.id, a.label)}
                        >
                          <span>{a.label}</span>
                        </button>
                      ))}
                  </div>
                )}
              </div>
            );
          })}

          {/* Si no hay fotos en este ambiente */}
          {fotosAmbienteActivo.length === 0 && !previewNuevo && (
            <div className="disenador-ia-no-photos-box">
              {esPropietario ? (
                <span>No hay fotos asignadas a <strong>{ambienteObj.label}</strong>. Sube una fotografía arriba para comenzar el amoblado virtual.</span>
              ) : (
                <span>No hay fotografías publicadas para <strong>{ambienteObj.label}</strong> en este inmueble.</span>
              )}
            </div>
          )}
        </div>

        {/* Opción de guardar en inmueble si es propietario y subió foto */}
        {esPropietario && archivoNuevo && (
          <label className="disenador-ia-checkbox-wrapper">
            <input
              type="checkbox"
              checked={guardarEnInmueble}
              onChange={(e) => setGuardarEnInmueble(e.target.checked)}
            />
            <span>Guardar esta nueva fotografía como "{ambienteObj.label}" en la galería oficial del inmueble</span>
          </label>
        )}
      </div>

      {/* ─── 3. Indicaciones de Diseño (Texto / Voz) ───────────────────────── */}
      <div className="disenador-ia-section">
        <div className="disenador-ia-section-title">
          <Sparkles size={16} />
          <span>3. Indicaciones de diseño y estilo para {ambienteObj.label}:</span>
        </div>

        <div className="disenador-ia-prompt-card">
          <textarea
            className="disenador-ia-textarea"
            placeholder={ambienteObj.placeholder}
            value={promptTexto}
            onChange={(e) => setPromptTexto(e.target.value)}
            rows={3}
          />

          <div className="disenador-ia-prompt-actions">
            {soportaVoz && (
              <button
                type="button"
                className={`disenador-ia-voice-btn ${escuchandoVoz ? 'recording' : ''}`}
                onClick={toggleGrabacionVoz}
                title={escuchandoVoz ? 'Detener micrófono' : 'Dictar por voz'}
              >
                {escuchandoVoz ? <MicOff size={16} /> : <Mic size={16} />}
                <span>{escuchandoVoz ? 'Escuchando voz...' : 'Dictar por voz'}</span>
              </button>
            )}

            <button
              type="button"
              className="disenador-ia-submit-btn"
              onClick={handleGenerarAmoblado}
              disabled={cargando}
            >
              {cargando ? (
                <>
                  <RefreshCw size={17} className="spin-icon" />
                  <span>Amoblando con IA...</span>
                </>
              ) : (
                <>
                  <Wand2 size={17} />
                  <span>Amoblar {ambienteObj.label}</span>
                </>
              )}
            </button>
          </div>
        </div>

        {/* Banner animado al dictar con voz */}
        {escuchandoVoz && (
          <div className="disenador-ia-voice-indicator">
            <div className="disenador-ia-voice-dot"></div>
            <span>Micrófono activado: Describe colores, texturas o muebles deseados para {ambienteObj.label}...</span>
          </div>
        )}
      </div>


      {/* ─── Alertas de Estado ────────────────────────────────────────────── */}
      {mensajeExito && (
        <div className="disenador-ia-alert success">
          <CheckCircle2 size={18} />
          <span>{mensajeExito}</span>
        </div>
      )}

      {mensajeError && (
        <div className="disenador-ia-alert error">
          <AlertCircle size={18} />
          <span>{mensajeError}</span>
        </div>
      )}

      {/* ─── 5. Comparador Antes / Después Split-Screen ────────────────────── */}
      <div className="disenador-ia-section">
        <AntesDespuesSlider
          imagenOriginal={fotoOriginalEfectiva}
          amoblados={amoblados}
          estiloInicial={estiloSeleccionado}
          onSelectEstilo={(estilo) => setEstiloSeleccionado(estilo)}
        />
      </div>

      {/* ─── 6. Ficha de Desglose de Interiorismo Arquitectónico ───────────── */}
      {detalleDiseno && (
        <div className="disenador-ia-breakdown-card">
          <div className="disenador-ia-breakdown-header">
            <Palette size={18} />
            <h4>Propuesta de Interiorismo: {detalleDiseno.estilo_nombre || 'Personalizado'}</h4>
          </div>

          <p className="disenador-ia-breakdown-desc">
            {detalleDiseno.descripcion}
          </p>

          {/* Paleta Cromática */}
          {Array.isArray(detalleDiseno.paleta_colores) && detalleDiseno.paleta_colores.length > 0 && (
            <div className="disenador-ia-palette-group">
              <span className="disenador-ia-group-label">Paleta de Colores Recomendada:</span>
              <div className="disenador-ia-palette-swatches">
                {detalleDiseno.paleta_colores.map((hex, idx) => (
                  <div key={idx} className="disenador-ia-swatch" title={hex}>
                    <span className="disenador-ia-swatch-box" style={{ backgroundColor: hex }}></span>
                    <span className="disenador-ia-swatch-code">{hex}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Mobiliario Principal */}
          {Array.isArray(detalleDiseno.mobiliario_principal) && detalleDiseno.mobiliario_principal.length > 0 && (
            <div className="disenador-ia-furniture-group">
              <span className="disenador-ia-group-label">Mobiliario y Materiales Clave:</span>
              <div className="disenador-ia-furniture-tags">
                {detalleDiseno.mobiliario_principal.map((mueble, idx) => (
                  <div key={idx} className="disenador-ia-furniture-tag">
                    <CheckCircle2 size={14} />
                    <span>{mueble}</span>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Iluminación & Consejo */}
          <div className="disenador-ia-advice-grid">
            {detalleDiseno.iluminacion && (
              <div className="disenador-ia-advice-item">
                <Lamp size={16} />
                <div>
                  <strong>Esquema Lumínico:</strong>
                  <p>{detalleDiseno.iluminacion}</p>
                </div>
              </div>
            )}
            {detalleDiseno.sugerencia_decorativa && (
              <div className="disenador-ia-advice-item tip">
                <Lightbulb size={16} />
                <div>
                  <strong>Valorización Inmobiliaria:</strong>
                  <p>{detalleDiseno.sugerencia_decorativa}</p>
                </div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default DisenadorInterioresIA;
