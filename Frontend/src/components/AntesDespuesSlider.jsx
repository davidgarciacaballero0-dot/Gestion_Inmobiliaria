import { useState, useRef, useCallback, useEffect } from 'react';
import { Sparkles, MoveHorizontal, Info, Layers } from 'lucide-react';
import './AntesDespuesSlider.css';

/**
 * AntesDespuesSlider — Comparador interactivo "Split-Screen" para Amoblado Virtual con IA.
 *
 * @param {object} props
 * @param {string} props.imagenOriginal - URL de la fotografía vacía original
 * @param {Array<object>} [props.amoblados] - Lista de amoblados generados disponibles
 * @param {string} [props.estiloInicial] - 'moderno' | 'minimalista' | 'ejecutivo' | 'boliviano'
 * @param {Function} [props.onSelectEstilo] - Callback al cambiar estilo
 */
const AntesDespuesSlider = ({
  imagenOriginal,
  amoblados = [],
  estiloInicial = 'moderno',
  onSelectEstilo,
}) => {
  const [sliderPosition, setSliderPosition] = useState(50); // porcentaje 0-100
  const [isDragging, setIsDragging] = useState(false);
  const [estiloActivo, setEstiloActivo] = useState(estiloInicial);
  const containerRef = useRef(null);

  const ESTILOS_INFO = {
    moderno: {
      nombre: 'Moderno',
      descripcion: 'Mobiliario vanguardista de líneas limpias, sofá modular en lino gris, mesa de vidrio templado e iluminación ambiental LED.',
      imgDefault: 'https://images.unsplash.com/photo-1600210492486-724fe5c67fb0?auto=format&fit=crop&w=1600&q=80',
    },
    minimalista: {
      nombre: 'Minimalista',
      descripcion: 'Espacios despejados con paleta neutra en blanco nórdico y madera roble. Muebles suspendidos y ausencia de saturación visual.',
      imgDefault: 'https://images.unsplash.com/photo-1598928506311-c55ded91a20c?auto=format&fit=crop&w=1600&q=80',
    },
    ejecutivo: {
      nombre: 'Ejecutivo',
      descripcion: 'Escritorio de madera nogal con acabados en bronce cepillado, sillón ergonómico de cuero genuino y biblioteca empotrada.',
      imgDefault: 'https://images.unsplash.com/photo-1618221195710-dd6b41faaea6?auto=format&fit=crop&w=1600&q=80',
    },
    boliviano: {
      nombre: 'Boliviano',
      descripcion: 'Diseño contemporáneo con madera Mara tallada a mano, sutiles textiles andinos en lana de alpaca y cerámica artesanal chiquitana.',
      imgDefault: 'https://images.unsplash.com/photo-1616486338812-3dadae4b4ace?auto=format&fit=crop&w=1600&q=80',
    },
  };

  // Determinar la imagen amoblada correspondiente al estilo seleccionado
  const amobladoEncontrado = amoblados.find((a) => a.estilo === estiloActivo);
  const imagenAmobladaActual = amobladoEncontrado?.imagen_amoblada || ESTILOS_INFO[estiloActivo]?.imgDefault;
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

  useEffect(() => {
    const handlePointerMove = (e) => {
      if (!isDragging) return;
      handleMove(e.clientX || (e.touches && e.touches[0]?.clientX));
    };

    const handlePointerUp = () => {
      if (isDragging) setIsDragging(false);
    };

    if (isDragging) {
      window.addEventListener('pointermove', handlePointerMove);
      window.addEventListener('pointerup', handlePointerUp);
      window.addEventListener('touchmove', handlePointerMove);
      window.addEventListener('touchend', handlePointerUp);
    }

    return () => {
      window.removeEventListener('pointermove', handlePointerMove);
      window.removeEventListener('pointerup', handlePointerUp);
      window.removeEventListener('touchmove', handlePointerMove);
      window.removeEventListener('touchend', handlePointerUp);
    };
  }, [isDragging, handleMove]);

  useEffect(() => {
    if (estiloInicial) {
      setEstiloActivo(estiloInicial);
    }
  }, [estiloInicial]);

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
        {Object.entries(ESTILOS_INFO).map(([key, info]) => (
          <button
            key={key}
            className={`staging-style-btn ${estiloActivo === key ? 'active' : ''}`}
            onClick={() => handleEstiloChange(key)}
          >
            {info.nombre}
          </button>
        ))}
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
