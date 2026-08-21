import { useState, useRef, useCallback, useEffect } from 'react';
import { Sparkles, MoveHorizontal, Info, Layers, Layout, Briefcase, Map, Maximize } from 'lucide-react';
import './AntesDespuesSlider.css';

const MOCKUPS_POR_AMBIENTE = {
  sala: {
    moderno: 'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1600&q=80',
    minimalista: 'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1600&q=80',
    ejecutivo: 'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=1600&q=80',
    boliviano: 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1600&q=80',
  },
  dormitorio: {
    moderno: 'https://images.unsplash.com/photo-1616594039964-ae9021a400a0?auto=format&fit=crop&w=1600&q=80',
    minimalista: 'https://images.unsplash.com/photo-1505691938895-1758d7feb511?auto=format&fit=crop&w=1600&q=80',
    ejecutivo: 'https://images.unsplash.com/photo-1595526114035-0d45ed16cfbf?auto=format&fit=crop&w=1600&q=80',
    boliviano: 'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1600&q=80',
  },
  cocina: {
    moderno: 'https://images.unsplash.com/photo-1556911220-e15b29be8c8f?auto=format&fit=crop&w=1600&q=80',
    minimalista: 'https://images.unsplash.com/photo-1556909212-d5b604d0c90d?auto=format&fit=crop&w=1600&q=80',
    ejecutivo: 'https://images.unsplash.com/photo-1507089947368-19c1da9775ae?auto=format&fit=crop&w=1600&q=80',
    boliviano: 'https://images.unsplash.com/photo-1600585154526-990dced4db0d?auto=format&fit=crop&w=1600&q=80',
  },
  bano: {
    moderno: 'https://images.unsplash.com/photo-1584622650111-993a426fbf0a?auto=format&fit=crop&w=1600&q=80',
    minimalista: 'https://images.unsplash.com/photo-1507089947368-19c1da9775ae?auto=format&fit=crop&w=1600&q=80',
    ejecutivo: 'https://images.unsplash.com/photo-1600585154340-be6161a56a0c?auto=format&fit=crop&w=1600&q=80',
    boliviano: 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1600&q=80',
  },
};

/**
 * AntesDespuesSlider — Comparador interactivo "Split-Screen" para Amoblado Virtual con IA.
 *
 * @param {object} props
 * @param {string} props.imagenOriginal - URL de la fotografía vacía original
 * @param {Array<object>} [props.amoblados] - Lista de amoblados generados disponibles
 * @param {string} [props.estiloInicial] - 'moderno' | 'minimalista' | 'ejecutivo' | 'boliviano'
 * @param {string} [props.ambiente] - 'sala' | 'dormitorio' | 'cocina' | 'bano' etc.
 * @param {Function} [props.onSelectEstilo] - Callback al cambiar estilo
 */
const AntesDespuesSlider = ({
  imagenOriginal,
  amoblados = [],
  estiloInicial = 'moderno',
  ambiente = 'sala',
  onSelectEstilo,
}) => {
  const [sliderPosition, setSliderPosition] = useState(50); // porcentaje 0-100
  const [isDragging, setIsDragging] = useState(false);
  const [estiloActivo, setEstiloActivo] = useState(estiloInicial);
  const containerRef = useRef(null);

  const ESTILOS_INFO = {
    moderno: {
      nombre: 'Moderno',
      icon: Layout,
      descripcion: 'Mobiliario vanguardista de líneas limpias, sofá modular en lino gris, mesa de vidrio templado e iluminación ambiental LED.',
      imgDefault: 'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1600&q=80',
    },
    minimalista: {
      nombre: 'Minimalista',
      icon: Maximize,
      descripcion: 'Espacios despejados con paleta neutra en blanco nórdico y madera roble. Muebles suspendidos y ausencia de saturación visual.',
      imgDefault: 'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1600&q=80',
    },
    ejecutivo: {
      nombre: 'Ejecutivo',
      icon: Briefcase,
      descripcion: 'Escritorio de madera nogal con acabados en bronce cepillado, sillón ergonómico de cuero genuino y biblioteca empotrada.',
      imgDefault: 'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=1600&q=80',
    },
    boliviano: {
      nombre: 'Boliviano',
      icon: Map,
      descripcion: 'Diseño contemporáneo con madera Mara tallada a mano, sutiles textiles andinos en lana de alpaca y cerámica artesanal chiquitana.',
      imgDefault: 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1600&q=80',
    },
  };

  // Buscar mockup IA por ambiente y estilo
  const ambKey = Object.keys(MOCKUPS_POR_AMBIENTE).find(k => (ambiente || '').toLowerCase().includes(k)) || 'sala';
  const mockupDefault = MOCKUPS_POR_AMBIENTE[ambKey]?.[estiloActivo] || ESTILOS_INFO[estiloActivo]?.imgDefault;

  // Determinar la imagen amoblada correspondiente al estilo seleccionado (evitar que sea idéntica a imagenOriginal)
  const amobladoEncontrado = amoblados.find((a) => a.estilo === estiloActivo && a.imagen_amoblada && a.imagen_amoblada !== imagenOriginal);
  const imagenAmobladaActual = amobladoEncontrado?.imagen_amoblada || mockupDefault;
  const descripcionActual = amobladoEncontrado?.descripcion_estilo || ESTILOS_INFO[estiloActivo]?.descripcion;

  // Manejador del arrastre del slider
  const handleMove = useCallback((clientX) => {
    if (!containerRef.current) return;
    const rect = containerRef.current.getBoundingClientRect();
    const x = clientX - rect.left;
    let percent = (x / rect.width) * 100;
    if (percent < 0) percent = 0;
    if (percent > 100) percent = 100;
    setSliderPosition(percent);
  }, []);

  const handlePointerDown = () => setIsDragging(true);
  const handlePointerUp = () => setIsDragging(false);

  useEffect(() => {
    window.addEventListener('pointerup', handlePointerUp);
    window.addEventListener('pointermove', (e) => isDragging && handleMove(e.clientX));
    return () => {
      window.removeEventListener('pointerup', handlePointerUp);
      window.removeEventListener('pointermove', (e) => isDragging && handleMove(e.clientX));
    };
  }, [isDragging, handleMove]);

  // Si amoblados cambia y no hay amobladoEncontrado para el estilo activo, 
  // pero sí hay uno recién generado, autoseleccionar el último
  useEffect(() => {
    if (amoblados.length > 0) {
      const ultimo = amoblados[amoblados.length - 1];
      setEstiloActivo(ultimo.estilo);
    }
  }, [amoblados]);

  const handleEstiloChange = (estiloKey) => {
    setEstiloActivo(estiloKey);
    if (onSelectEstilo) {
      onSelectEstilo(estiloKey);
    }
  };

  return (
    <div className="staging-slider-wrapper">
      {/* Selector de Estilos */}
      <div className="staging-style-selector">
        <span className="staging-style-title">
          <Sparkles size={14} style={{ display: 'inline', marginRight: 4, color: '#0ea5e9' }} />
          Estilo de Amoblado:
        </span>
        {Object.entries(ESTILOS_INFO).map(([key, info]) => {
          const Icon = info.icon;
          return (
            <button
              key={key}
              className={`staging-style-btn ${estiloActivo === key ? 'active' : ''}`}
              onClick={() => handleEstiloChange(key)}
            >
              <Icon size={14} style={{ marginRight: 6 }} />
              {info.nombre}
            </button>
          );
        })}
      </div>

      {/* Canvas de Comparación Split-Screen */}
      <div
        ref={containerRef}
        className="staging-canvas-container"
        onPointerDown={(e) => {
          handlePointerDown();
          handleMove(e.clientX);
        }}
      >
        {/* Imagen Base (Amoblada / Después) */}
        <img
          src={imagenAmobladaActual}
          alt="Habitación Amoblada con IA"
          className="staging-image-base"
        />

        {/* Imagen Overlay con clip-path (Vacía / Antes) */}
        <img
          src={imagenOriginal || imagenAmobladaActual}
          alt="Habitación Vacía Original"
          className="staging-image-overlay"
          style={{
            clipPath: `polygon(0 0, ${sliderPosition}% 0, ${sliderPosition}% 100%, 0 100%)`,
            filter: 'brightness(0.95)',
          }}
        />

        {/* Badges Flotantes */}
        <span className="staging-badge antes">Vacío (Original)</span>
        <span className="staging-badge despues">Amoblado ({ESTILOS_INFO[estiloActivo]?.nombre})</span>

        {/* Línea Divisoria y Manija */}
        <div
          className="staging-divider-line"
          style={{ left: `${sliderPosition}%` }}
        >
          <div
            className="staging-divider-handle"
            onPointerDown={handlePointerDown}
          >
            <MoveHorizontal size={20} />
          </div>
        </div>
      </div>

      {/* Pie Informativo de los muebles incorporados */}
      <div className="staging-info-footer">
        <div className="staging-info-icon">
          <Info size={18} />
        </div>
        <p className="staging-info-text">
          <strong>Propuesta de Diseño IA:</strong> {descripcionActual}
        </p>
      </div>
    </div>
  );
};

export default AntesDespuesSlider;
