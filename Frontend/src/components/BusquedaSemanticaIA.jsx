import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import {
  Sparkles,
  Camera,
  UploadCloud,
  X,
  Search,
  Building,
  CheckCircle2,
  MapPin,
  SlidersHorizontal,
  ChevronRight,
  Trash2,
  Layers,
  Palette,
  DollarSign,
  TrendingDown,
} from 'lucide-react';
import busquedaSemanticaService from '../services/busquedaSemanticaService';
import './BusquedaSemanticaIA.css';

const SUGERENCIAS_EJEMPLO = [
  'Departamento luminoso con vista panorámica y balcón',
  'Casa moderna de 3 dormitorios con jardín y parrillero',
  'Monoambiente amoblado para estudiante cerca de universidad',
  'Oficina ejecutiva con garaje y seguridad en zona comercial',
];

export default function BusquedaSemanticaIA({ onClose, onSelectPropiedad }) {
  const [descripcion, setDescripcion] = useState('');
  const [fotoArchivo, setFotoArchivo] = useState(null);
  const [fotoPreview, setFotoPreview] = useState(null);
  const [tipoOferta, setTipoOferta] = useState('');
  const [precioMax, setPrecioMax] = useState('');

  const [loading, setLoading] = useState(false);
  const [resultados, setResultados] = useState([]);
  const [estilosDetectados, setEstilosDetectados] = useState([]);
  const [busquedaRealizada, setBusquedaRealizada] = useState(false);
  const [errorMsg, setErrorMsg] = useState(null);

  const fileInputRef = useRef(null);

  // Bloquear scroll de la página de fondo al abrir el modal
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // Manejar selección de foto
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      setFotoArchivo(file);
      setFotoPreview(URL.createObjectURL(file));
    }
  };

  const handleQuitarFoto = () => {
    setFotoArchivo(null);
    setFotoPreview(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleBuscar = async (e) => {
    if (e) e.preventDefault();
    if (!descripcion.trim() && !fotoArchivo) {
      setErrorMsg('Por favor escribe una descripción o sube una fotografía de referencia.');
      return;
    }

    setLoading(true);
    setErrorMsg(null);
    try {
      const resp = await busquedaSemanticaService.buscarSemanticaIA({
        descripcion: descripcion.trim(),
        foto: fotoArchivo,
        tipo_oferta: tipoOferta || undefined,
        precio_max: precioMax ? parseFloat(precioMax) : undefined,
      });

      setResultados(resp.resultados || []);
      setEstilosDetectados(resp.estilos_detectados || []);
      setBusquedaRealizada(true);
    } catch (err) {
      console.error('Error en búsqueda semántica IA:', err);
      setErrorMsg('No se pudo procesar la búsqueda semántica. Intenta con otros términos.');
    } finally {
      setLoading(false);
    }
  };

  return createPortal(
    <div className="semantica-modal-overlay">
      <div className="semantica-modal-card">
        {/* Cabecera Profesional */}
        <div className="semantica-modal-header">
          <div className="header-brand-group">
            <div className="header-icon-box">
              <Sparkles size={22} className="header-icon-svg" />
            </div>
            <div>
              <h3>Búsqueda por Foto o Lenguaje Natural (IA)</h3>
              <p>Describe tu propiedad ideal en tus propias palabras o sube una foto de referencia arquitectónica</p>
            </div>
          </div>
          <button className="btn-close-semantica" onClick={onClose} title="Cerrar modal">
            <X size={20} />
          </button>
        </div>

        {/* Cuerpo Modal en 2 Columnas (Buscador Izq / Resultados Der) */}
        <div className="semantica-modal-body">
          {/* Columna Izquierda: Formulario de Entrada */}
          <div className="semantica-input-col">
            {/* Sección Subida de Foto */}
            <div className="semantica-section-card">
              <label className="section-title-label">
                <Camera size={16} />
                <span>1. Foto o Imagen de Referencia (Opcional)</span>
              </label>

              {!fotoPreview ? (
                <div
                  className="photo-dropzone"
                  onClick={() => fileInputRef.current?.click()}
                >
                  <UploadCloud size={32} className="dropzone-icon" />
                  <p className="dropzone-text">
                    Haz clic o arrastra una imagen de referencia aquí
                  </p>
                  <span className="dropzone-sub">Formatos JPG, PNG o WEBP (Diseños, Pinterest o Capturas)</span>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/*"
                    onChange={handleFileChange}
                    style={{ display: 'none' }}
                  />
                </div>
              ) : (
                <div className="photo-preview-box">
                  <img src={fotoPreview} alt="Referencia visual" className="preview-img" />
                  <div className="preview-info">
                    <span className="preview-name">{fotoArchivo?.name || 'Foto seleccionada'}</span>
                    <button type="button" className="btn-remove-photo" onClick={handleQuitarFoto}>
                      <Trash2 size={14} />
                      <span>Quitar foto</span>
                    </button>
                  </div>
                </div>
              )}
            </div>

            {/* Sección Descripción en Lenguaje Natural */}
            <div className="semantica-section-card">
              <label className="section-title-label">
                <Search size={16} />
                <span>2. Descripción en Lenguaje Natural</span>
              </label>
              <textarea
                className="natural-textarea"
                rows={3}
                placeholder="Ejemplo: Busco departamento moderno, piso alto con mucha luz natural, cocina americana con isla y cerca de avenidas..."
                value={descripcion}
                onChange={(e) => setDescripcion(e.target.value)}
              />

              {/* Sugerencias Rápidas */}
              <div className="suggestions-container">
                <span className="suggestions-label">Ideas de búsqueda rápida:</span>
                <div className="suggestions-chips">
                  {SUGERENCIAS_EJEMPLO.map((sug, idx) => (
                    <button
                      key={idx}
                      type="button"
                      className="chip-suggestion"
                      onClick={() => setDescripcion(sug)}
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            {/* Filtros Complementarios */}
            <div className="semantica-section-card">
              <label className="section-title-label">
                <SlidersHorizontal size={16} />
                <span>3. Filtros Complementarios</span>
              </label>
              <div className="filters-grid-sm">
                <div>
                  <label className="filter-label-sm">Tipo de Oferta</label>
                  <select
                    className="filter-select-sm"
                    value={tipoOferta}
                    onChange={(e) => setTipoOferta(e.target.value)}
                  >
                    <option value="">Todas las ofertas</option>
                    <option value="alquiler">Alquiler</option>
                    <option value="venta">Venta</option>
                    <option value="anticretico">Anticrético</option>
                  </select>
                </div>
                <div>
                  <label className="filter-label-sm">Presupuesto Máx (USD)</label>
                  <input
                    type="number"
                    className="filter-input-sm"
                    placeholder="Ej. 1200"
                    value={precioMax}
                    onChange={(e) => setPrecioMax(e.target.value)}
                  />
                </div>
              </div>
            </div>

            {/* Botón Principal de Búsqueda */}
            <button
              type="button"
              className="btn-search-semantic"
              onClick={handleBuscar}
              disabled={loading}
            >
              <Sparkles size={18} />
              <span>{loading ? 'Analizando con IA Multimodal...' : 'Buscar Propiedades con IA'}</span>
            </button>

            {errorMsg && <div className="semantica-error-banner">{errorMsg}</div>}
          </div>

          {/* Columna Derecha: Resultados de Coincidencia */}
          <div className="semantica-results-col">
            <div className="results-col-header">
              <div>
                <h4>Resultados por Afinidad Semántica ({resultados.length})</h4>
                <span className="results-subtext">Ordenado por % de Coincidencia y Estilos Arquitectónicos</span>
              </div>
            </div>

            {/* Estilos Arquitectónicos Detectados por IA */}
            {estilosDetectados.length > 0 && (
              <div className="styles-detected-bar">
                <div className="styles-title-row">
                  <Palette size={14} />
                  <span>Estilos y Elementos Arquitectónicos Detectados:</span>
                </div>
                <div className="styles-chips-row">
                  {estilosDetectados.map((st, idx) => (
                    <span key={idx} className="chip-style-detected">
                      {st}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {!busquedaRealizada && !loading && (
              <div className="results-empty-guide">
                <Building size={48} className="empty-guide-icon" />
                <h5>Explora el catálogo con Inteligencia Artificial</h5>
                <p>
                  Escribe en tus propias palabras qué necesitas o sube una fotografía para encontrar opciones arquitectónicamente similares.
                </p>
              </div>
            )}

            {busquedaRealizada && resultados.length === 0 && !loading && (
              <div className="results-empty-guide">
                <Layers size={48} className="empty-guide-icon" />
                <h5>No se encontraron coincidencias cercanas</h5>
                <p>Intenta ampliar tu descripción o flexibilizar los filtros de precio y oferta.</p>
              </div>
            )}

            {loading && (
              <div className="results-loading-state">
                <Sparkles size={36} className="loading-pulse-svg" />
                <p>La IA está evaluando los atributos arquitectónicos y semánticos del catálogo...</p>
              </div>
            )}

            <div className="semantic-cards-grid">
              {resultados.map((prop) => {
                const matchClass =
                  prop.coincidencia_porcentaje >= 85
                    ? 'high'
                    : prop.coincidencia_porcentaje >= 65
                    ? 'mid'
                    : 'low';

                return (
                  <div
                    key={prop.inmueble_id}
                    className="semantic-prop-card"
                    onClick={() => onSelectPropiedad && onSelectPropiedad(prop.inmueble_id)}
                  >
                    <div className="prop-card-media">
                      <img
                        src={prop.imagen || 'https://via.placeholder.com/400x250?text=Inmueble'}
                        alt={prop.titulo}
                      />
                      <div className={`match-badge ${matchClass}`}>
                        <CheckCircle2 size={13} />
                        <span>{prop.coincidencia_porcentaje}% Coincidencia</span>
                      </div>
                    </div>

                    <div className="prop-card-content">
                      <div className="card-top-row">
                        <span className="card-type-tag">{prop.tipo}</span>
                        <span className="card-offer-tag">{prop.tipo_oferta}</span>
                        {prop.es_lookalike_economico && (
                          <span className="lookalike-badge-pro">
                            <TrendingDown size={11} /> Look-alike accesible
                          </span>
                        )}
                      </div>

                      <h5 className="prop-title">{prop.titulo}</h5>

                      <p className="prop-location">
                        <MapPin size={13} />
                        <span>{prop.direccion}</span>
                      </p>

                      <div className="prop-price-row">
                        <span className="price-val">
                          {prop.precio ? `$${prop.precio} USD` : 'Consultar'}
                        </span>
                        <div className="prop-specs-pills">
                          {prop.habitaciones && <span>{prop.habitaciones} Hab</span>}
                          {prop.banos && <span>{prop.banos} Baños</span>}
                          {prop.superficie && <span>{prop.superficie} m²</span>}
                        </div>
                      </div>

                      {/* Atributos coincidentes */}
                      {prop.atributos_coincidentes && prop.atributos_coincidentes.length > 0 && (
                        <div className="matching-features-row">
                          {prop.atributos_coincidentes.map((tag, idx) => (
                            <span key={idx} className="match-tag">
                              ✓ {tag}
                            </span>
                          ))}
                        </div>
                      )}

                      {/* Justificación ejecutiva de la IA */}
                      {prop.justificacion_ia && (
                        <div className="ai-justification-box">
                          <div className="justification-header">
                            <Sparkles size={13} />
                            <span>Dictamen IA:</span>
                          </div>
                          <p>{prop.justificacion_ia}</p>
                        </div>
                      )}

                      <button
                        type="button"
                        className="btn-view-prop-detail"
                        onClick={(e) => {
                          e.stopPropagation();
                          if (onSelectPropiedad) onSelectPropiedad(prop.inmueble_id);
                        }}
                      >
                        <span>Ver Ficha del Inmueble</span>
                        <ChevronRight size={15} />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    </div>,
    document.body
  );
}
