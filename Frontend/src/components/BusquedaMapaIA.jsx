import React, { useState, useEffect, useRef } from 'react';
import { createPortal } from 'react-dom';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import {
  MapPin,
  Briefcase,
  Users,
  GraduationCap,
  Dumbbell,
  ShoppingCart,
  Target,
  Sparkles,
  Car,
  Search,
  X,
  Plus,
  SlidersHorizontal,
  ChevronRight,
  ChevronLeft,
  Building,
  CheckCircle,
  AlertCircle,
  Compass,
  Edit3,
  Trash2,
  Clock,
  Zap,
} from 'lucide-react';
import mapaBusquedaService from '../services/mapaBusquedaService';
import './BusquedaMapaIA.css';

// Fix para íconos por defecto de Leaflet en Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Ciudades principales de Bolivia con coordenadas centrales
const CIUDADES_BOLIVIA = [
  { id: 'cbba', nombre: 'Cochabamba', lat: -17.3935, lng: -66.1570 },
  { id: 'scz', nombre: 'Santa Cruz de la Sierra', lat: -17.7833, lng: -63.1821 },
  { id: 'lpz', nombre: 'La Paz', lat: -16.5000, lng: -68.1500 },
  { id: 'eal', nombre: 'El Alto', lat: -16.5000, lng: -68.1900 },
  { id: 'trj', nombre: 'Tarija', lat: -21.5355, lng: -64.7296 },
  { id: 'suc', nombre: 'Sucre', lat: -19.0333, lng: -65.2627 },
  { id: 'oru', nombre: 'Oruro', lat: -17.9833, lng: -67.1500 },
  { id: 'pts', nombre: 'Potosí', lat: -19.5833, lng: -65.7500 },
  { id: 'ben', nombre: 'Trinidad (Beni)', lat: -14.8333, lng: -64.9000 },
];

// Barrios / Macrodistritos populares de Bolivia con polígonos reales
const BARRIOS_BOLIVIA = {
  cbba: [
    { nombre: 'Cala Cala', coords: [[-17.375, -66.168], [-17.370, -66.155], [-17.382, -66.152], [-17.385, -66.165]] },
    { nombre: 'Sarco', coords: [[-17.380, -66.185], [-17.372, -66.175], [-17.388, -66.170], [-17.392, -66.182]] },
    { nombre: 'Recoleta / Queru Queru', coords: [[-17.370, -66.152], [-17.362, -66.142], [-17.375, -66.138], [-17.380, -66.148]] },
    { nombre: 'América Oeste', coords: [[-17.378, -66.172], [-17.374, -66.160], [-17.385, -66.158], [-17.388, -66.170]] },
  ],
  scz: [
    { nombre: 'Equipetrol', coords: [[-17.765, -63.198], [-17.755, -63.190], [-17.770, -63.180], [-17.778, -63.192]] },
    { nombre: 'Urbarí', coords: [[-17.795, -63.205], [-17.785, -63.198], [-17.798, -63.188], [-17.808, -63.195]] },
    { nombre: 'Las Palmas', coords: [[-17.805, -63.215], [-17.795, -63.205], [-17.810, -63.195], [-17.820, -63.208]] },
    { nombre: 'Sirari', coords: [[-17.760, -63.195], [-17.750, -63.185], [-17.765, -63.175], [-17.772, -63.188]] },
  ],
  lpz: [
    { nombre: 'Sopocachi', coords: [[-16.518, -68.132], [-16.508, -68.125], [-16.515, -68.118], [-16.525, -68.125]] },
    { nombre: 'Calacoto', coords: [[-16.545, -68.085], [-16.535, -68.075], [-16.550, -68.065], [-16.560, -68.078]] },
    { nombre: 'San Miguel', coords: [[-16.542, -68.080], [-16.535, -68.072], [-16.548, -68.065], [-16.555, -68.074]] },
    { nombre: 'Miraflores', coords: [[-16.505, -68.125], [-16.495, -68.118], [-16.510, -68.110], [-16.518, -68.119]] },
  ]
};

const POI_TIPOS = [
  { id: 'trabajo', label: 'Trabajo', key: 'Briefcase', peso: 1.5 },
  { id: 'familia', label: 'Familia / Casa de Mamá', key: 'Users', peso: 1.0 },
  { id: 'educacion', label: 'Universidad / Colegio', key: 'GraduationCap', peso: 1.2 },
  { id: 'gimnasio', label: 'Gimnasio / Deportes', key: 'Dumbbell', peso: 0.8 },
  { id: 'compras', label: 'Supermercado / Compras', key: 'ShoppingCart', peso: 0.9 },
  { id: 'otro', label: 'Otro Punto de Interés', key: 'MapPin', peso: 1.0 },
];

export default function BusquedaMapaIA({ onClose, onSelectPropiedad }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const centerMarkerRef = useRef(null);
  const circleRef = useRef(null);
  const polygonLayerRef = useRef(null);
  const poiMarkersGroupRef = useRef(null);
  const propMarkersGroupRef = useRef(null);

  // Ciudad Seleccionada (Por defecto Cochabamba)
  const [ciudadSeleccionada, setCiudadSeleccionada] = useState(CIUDADES_BOLIVIA[0]);

  // Estados del filtro
  const [center, setCenter] = useState({ lat: CIUDADES_BOLIVIA[0].lat, lng: CIUDADES_BOLIVIA[0].lng });
  const [radioKm, setRadioKm] = useState(5.0);
  const [tipoOferta, setTipoOferta] = useState('');
  const [precioMax, setPrecioMax] = useState('');

  // Modo Dibujo de Zona Libre (estilo InfoCasas)
  const [modoDibujo, setModoDibujo] = useState(false);
  const [poligonoPuntos, setPoligonoPuntos] = useState([]);
  const [barrioActivo, setBarrioActivo] = useState(null);

  // Puntos de Interés limpios por defecto
  const [pois, setPois] = useState([]);

  // Formulario nuevo POI
  const [nuevoPoiNombre, setNuevoPoiNombre] = useState('');
  const [nuevoPoiTipo, setNuevoPoiTipo] = useState(POI_TIPOS[0]);
  const [modoSeleccionarPoiEnMapa, setModoSeleccionarPoiEnMapa] = useState(false);

  // Búsqueda por dirección (Nominatim Geocoding en Bolivia)
  const [busquedaDireccionText, setBusquedaDireccionText] = useState('');
  const [buscandoDireccion, setBuscandoDireccion] = useState(false);
  const [direccionStatus, setDireccionStatus] = useState(null);

  // Resultados
  const [loading, setLoading] = useState(false);
  const [resultados, setResultados] = useState([]);
  const [propiedadSeleccionada, setPropiedadSeleccionada] = useState(null);
  const [panelResultadosAbierto, setPanelResultadosAbierto] = useState(true);
  const [errorMsg, setErrorMsg] = useState(null);

  // Bloquear scroll de la página de fondo al abrir el modal
  useEffect(() => {
    document.body.style.overflow = 'hidden';
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, []);

  // 1. Inicializar Mapa Leaflet
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    const map = L.map(mapRef.current, {
      center: [center.lat, center.lng],
      zoom: 13,
      zoomControl: true,
    });

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19,
      attribution: '&copy; OpenStreetMap',
    }).addTo(map);

    poiMarkersGroupRef.current = L.layerGroup().addTo(map);
    propMarkersGroupRef.current = L.layerGroup().addTo(map);

    mapInstanceRef.current = map;

    // Listener para clic en el mapa
    map.on('click', (e) => {
      const { lat, lng } = e.latlng;
      if (window._isDrawingPolygon) {
        window._onAddPolygonPoint(lat, lng);
      } else if (window._isAddingPoi) {
        window._onPoiLocationSelected(lat, lng);
      } else {
        setCenter({ lat, lng });
      }
    });

    setTimeout(() => {
      map.invalidateSize();
    }, 200);

    return () => {
      map.remove();
      mapInstanceRef.current = null;
    };
  }, []);

  // 2. Cambiar de Ciudad Seleccionada
  const handleCambiarCiudad = (ciudadObj) => {
    setCiudadSeleccionada(ciudadObj);
    const newCenter = { lat: ciudadObj.lat, lng: ciudadObj.lng };
    setCenter(newCenter);
    setPoligonoPuntos([]);
    setBarrioActivo(null);
    if (mapInstanceRef.current) {
      mapInstanceRef.current.flyTo([ciudadObj.lat, ciudadObj.lng], 13);
    }
  };

  // 3. Renderizar Centro / Círculo o Polígono Dibujado
  useEffect(() => {
    const map = mapInstanceRef.current;
    if (!map) return;

    if (centerMarkerRef.current) map.removeLayer(centerMarkerRef.current);
    if (circleRef.current) map.removeLayer(circleRef.current);
    if (polygonLayerRef.current) map.removeLayer(polygonLayerRef.current);

    if (poligonoPuntos.length >= 3) {
      // Renderizar Polígono delimitado estilo InfoCasas
      polygonLayerRef.current = L.polygon(poligonoPuntos, {
        color: '#ea580c',
        weight: 3,
        fillColor: '#f97316',
        fillOpacity: 0.22,
        dashArray: modoDibujo ? '6, 6' : undefined,
      }).addTo(map);

      if (!modoDibujo) {
        map.fitBounds(polygonLayerRef.current.getBounds(), { padding: [40, 40] });
      }
    } else {
      // Marcador del centro
      const centerIcon = L.divIcon({
        className: 'custom-center-pin',
        html: `<div class="center-target-node"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><circle cx="12" cy="12" r="10"/><circle cx="12" cy="12" r="4"/></svg></div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      centerMarkerRef.current = L.marker([center.lat, center.lng], { icon: centerIcon }).addTo(map);
      centerMarkerRef.current.bindPopup('<b>Centro de Búsqueda</b><br/>Haz clic en cualquier punto para cambiar la zona');

      // Círculo de radio
      circleRef.current = L.circle([center.lat, center.lng], {
        color: '#2563eb',
        fillColor: '#3b82f6',
        fillOpacity: 0.12,
        weight: 2,
        radius: radioKm * 1000,
      }).addTo(map);
    }
  }, [center, radioKm, poligonoPuntos, modoDibujo]);

  // 4. Renderizar Marcadores de Puntos de Interés (POIs)
  useEffect(() => {
    const group = poiMarkersGroupRef.current;
    if (!group) return;

    group.clearLayers();

    pois.forEach((poi) => {
      const icon = L.divIcon({
        className: 'custom-poi-pin',
        html: `<div class="poi-bubble-clean"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#2563eb" stroke-width="2.5"><path d="M21 10c0 7-9 13-9 13s-9-6-9-13a9 9 0 0 1 18 0z"/><circle cx="12" cy="10" r="3"/></svg></div>`,
        iconSize: [28, 28],
        iconAnchor: [14, 14],
      });

      const marker = L.marker([poi.lat, poi.lng], { icon }).addTo(group);
      marker.bindPopup(`<b>${poi.nombre}</b><br/>Punto de Interés`);
    });
  }, [pois]);

  // 5. Renderizar Marcadores de Propiedades Encontradas
  useEffect(() => {
    const group = propMarkersGroupRef.current;
    if (!group) return;

    group.clearLayers();

    resultados.forEach((item) => {
      const isSelected = propiedadSeleccionada?.inmueble_id === item.inmueble_id;
      const scoreClass = item.score_conveniencia >= 80 ? 'high' : item.score_conveniencia >= 60 ? 'mid' : 'low';

      const icon = L.divIcon({
        className: `custom-prop-pin ${isSelected ? 'selected' : ''}`,
        html: `<div class="score-badge-clean ${scoreClass}">${item.score_conveniencia} pts</div>`,
        iconSize: [60, 26],
        iconAnchor: [30, 13],
      });

      const marker = L.marker([item.lat, item.lng], { icon }).addTo(group);
      marker.bindPopup(`
        <div style="font-family: system-ui; padding: 2px;">
          <b style="color: #0f172a;">${item.titulo}</b><br/>
          <span style="color: #2563eb; font-weight: 700;">Score: ${item.score_conveniencia}/100</span><br/>
          ${item.precio ? `<span style="font-weight: 600;">$${item.precio} USD</span>` : ''}
        </div>
      `);

      marker.on('click', () => {
        setPropiedadSeleccionada(item);
        setPanelResultadosAbierto(true);
      });
    });
  }, [resultados, propiedadSeleccionada]);

  // 6. Manejo de Dibujo Libre y Marcado de POI
  useEffect(() => {
    const mapContainer = mapRef.current;
    if (!mapContainer) return;

    if (modoDibujo) {
      mapContainer.classList.add('map-drawing-active');
    } else if (modoSeleccionarPoiEnMapa) {
      mapContainer.classList.add('map-picking-active');
    } else {
      mapContainer.classList.remove('map-drawing-active');
      mapContainer.classList.remove('map-picking-active');
    }

    window._isDrawingPolygon = modoDibujo;
    window._onAddPolygonPoint = (lat, lng) => {
      setPoligonoPuntos((prev) => [...prev, [lat, lng]]);
    };

    window._isAddingPoi = modoSeleccionarPoiEnMapa;
    window._onPoiLocationSelected = (lat, lng) => {
      const nombre = nuevoPoiNombre.trim() || nuevoPoiTipo.label;
      const newPoi = {
        id: Date.now(),
        nombre,
        lat,
        lng,
        tipo: nuevoPoiTipo.id,
        peso: nuevoPoiTipo.peso,
      };
      setPois((prev) => [...prev, newPoi]);
      setNuevoPoiNombre('');
      setModoSeleccionarPoiEnMapa(false);
    };
  }, [modoDibujo, modoSeleccionarPoiEnMapa, nuevoPoiNombre, nuevoPoiTipo]);

  // Manejador para eliminar el dibujo (estilo InfoCasas)
  const handleEliminarDibujo = () => {
    setPoligonoPuntos([]);
    setModoDibujo(false);
    setBarrioActivo(null);
  };

  // Manejador para seleccionar un barrio predefinido de Bolivia
  const handleSeleccionarBarrio = (barrio) => {
    if (barrioActivo === barrio.nombre) {
      handleEliminarDibujo();
      return;
    }
    setBarrioActivo(barrio.nombre);
    setPoligonoPuntos(barrio.coords);
    setModoDibujo(false);
  };

  // Búsqueda de dirección con Nominatim Geocoding en Bolivia
  const handleBuscarDireccionPOI = async (e) => {
    e.preventDefault();
    if (!busquedaDireccionText.trim()) return;

    setBuscandoDireccion(true);
    setDireccionStatus(null);
    try {
      const queryText = `${busquedaDireccionText.trim()}, ${ciudadSeleccionada.nombre}, Bolivia`;
      const url = `https://nominatim.openstreetmap.org/search?format=json&countrycodes=bo&q=${encodeURIComponent(queryText)}`;
      const res = await fetch(url, { headers: { 'User-Agent': 'AutogestionInmobiliaria/2.0' } });
      let data = await res.json();

      if (!data || data.length === 0) {
        const urlFallback = `https://nominatim.openstreetmap.org/search?format=json&countrycodes=bo&q=${encodeURIComponent(busquedaDireccionText.trim() + ', Bolivia')}`;
        const resFb = await fetch(urlFallback, { headers: { 'User-Agent': 'AutogestionInmobiliaria/2.0' } });
        data = await resFb.json();
      }

      if (data && data.length > 0) {
        const match = data[0];
        const lat = parseFloat(match.lat);
        const lng = parseFloat(match.lon);

        const newPoi = {
          id: Date.now(),
          nombre: busquedaDireccionText.trim(),
          lat,
          lng,
          tipo: nuevoPoiTipo.id,
          peso: nuevoPoiTipo.peso,
        };

        setPois((prev) => [...prev, newPoi]);
        setBusquedaDireccionText('');
        setDireccionStatus({ success: true, message: `Ubicado en ${ciudadSeleccionada.nombre}: ${match.display_name.split(',')[0]}` });

        if (mapInstanceRef.current) {
          mapInstanceRef.current.flyTo([lat, lng], 15);
        }
      } else {
        setDireccionStatus({ success: false, message: `No se encontró la dirección en ${ciudadSeleccionada.nombre}, Bolivia.` });
      }
    } catch (err) {
      console.error('Error geocodificando dirección:', err);
      setDireccionStatus({ success: false, message: 'Error de red consultando la dirección.' });
    } finally {
      setBuscandoDireccion(false);
    }
  };

  // Ejecutar búsqueda con IA (soporta Polígono o Radio)
  const handleBuscarConIA = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      const payload = {
        lat: center.lat,
        lng: center.lng,
        radio_km: parseFloat(radioKm),
        puntos_interes: pois,
        tipo_oferta: tipoOferta || undefined,
        precio_max: precioMax ? parseFloat(precioMax) : undefined,
        poligono_coords: poligonoPuntos.length >= 3 ? poligonoPuntos : undefined,
      };

      const resp = await mapaBusquedaService.buscarPorMapaIA(payload);
      setResultados(resp.resultados || []);
      if (resp.resultados && resp.resultados.length > 0) {
        setPropiedadSeleccionada(resp.resultados[0]);
        setPanelResultadosAbierto(true);
      } else {
        setPropiedadSeleccionada(null);
      }
    } catch (err) {
      console.error('Error buscando propiedades por mapa IA:', err);
      setErrorMsg('No se pudo procesar la búsqueda por mapa. Intenta ajustar la zona.');
    } finally {
      setLoading(false);
    }
  };

  const handleEliminarPoi = (id) => {
    setPois((prev) => prev.filter((p) => p.id !== id));
  };

  const barriosDisponibles = BARRIOS_BOLIVIA[ciudadSeleccionada.id] || [];

  return createPortal(
    <div className="busqueda-mapa-overlay">
      <div className="busqueda-mapa-modal">
        {/* Cabecera Profesional */}
        <div className="busqueda-mapa-header">
          <div className="header-title">
            <div className="header-icon-container">
              <MapPin size={22} className="header-svg-icon" />
            </div>
            <div>
              <h3>Búsqueda Geoespacial por Mapa con IA</h3>
              <p>Delimita zonas libres, explora barrios de Bolivia y calcula tu Score de Rutina Diaria</p>
            </div>
          </div>
          <button className="btn-close-modal" onClick={onClose} title="Cerrar modal">
            <X size={20} />
          </button>
        </div>

        {/* Cuerpo Principal de 3 Paneles */}
        <div className="busqueda-mapa-body-v2">
          {/* Panel 1: Sidebar de Configuración & POIs */}
          <div className="busqueda-sidebar-v2">
            {/* Selección de Ciudad / Departamento */}
            <div className="sidebar-section city-selector-box">
              <div className="section-title-row">
                <Compass size={16} className="section-icon" />
                <h4>Ciudad / Departamento</h4>
              </div>
              <select
                className="city-select-dropdown"
                value={ciudadSeleccionada.id}
                onChange={(e) => {
                  const sel = CIUDADES_BOLIVIA.find((c) => c.id === e.target.value);
                  if (sel) handleCambiarCiudad(sel);
                }}
              >
                {CIUDADES_BOLIVIA.map((ciudad) => (
                  <option key={ciudad.id} value={ciudad.id}>
                    {ciudad.nombre}
                  </option>
                ))}
              </select>
            </div>

            {/* Delimitación de Zona (Radio vs Dibujo Libre InfoCasas) */}
            <div className="sidebar-section">
              <div className="section-title-row">
                <Target size={16} className="section-icon" />
                <h4>1. Zona de Búsqueda</h4>
              </div>

              {/* Botón de Trazo Libre estilo InfoCasas */}
              <div className="zone-actions-bar">
                <button
                  type="button"
                  className={`btn-draw-zone ${modoDibujo ? 'active' : ''}`}
                  onClick={() => {
                    setModoDibujo(!modoDibujo);
                    if (!modoDibujo && poligonoPuntos.length === 0) {
                      setBarrioActivo(null);
                    }
                  }}
                >
                  <Edit3 size={15} />
                  <span>{modoDibujo ? 'Finalizar Dibujo' : 'Dibujar mi Zona'}</span>
                </button>
                {poligonoPuntos.length > 0 && (
                  <button
                    type="button"
                    className="btn-clear-draw-sm"
                    onClick={handleEliminarDibujo}
                    title="Eliminar trazado"
                  >
                    <Trash2 size={14} />
                    <span>Borrar</span>
                  </button>
                )}
              </div>

              {/* Selector de Barrios Populares de Bolivia */}
              {barriosDisponibles.length > 0 && (
                <div className="neighborhoods-quick-box">
                  <span className="sub-label-dim">Barrios y Zonas Populares:</span>
                  <div className="neighborhoods-chips-row">
                    {barriosDisponibles.map((b, idx) => (
                      <button
                        key={idx}
                        type="button"
                        className={`chip-neighborhood ${barrioActivo === b.nombre ? 'active' : ''}`}
                        onClick={() => handleSeleccionarBarrio(b)}
                      >
                        {b.nombre}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              {/* Modo Radio Circular */}
              {poligonoPuntos.length === 0 && (
                <div className="range-group">
                  <div className="range-header">
                    <span>Radio de Cobertura</span>
                    <strong>{radioKm} km</strong>
                  </div>
                  <input
                    type="range"
                    min="1"
                    max="15"
                    step="0.5"
                    value={radioKm}
                    onChange={(e) => setRadioKm(parseFloat(e.target.value))}
                  />
                  <p className="help-text-pro">
                    Haz clic en el mapa para ubicar el centro de tu zona en {ciudadSeleccionada.nombre}.
                  </p>
                </div>
              )}
            </div>

            {/* Puntos de Interés */}
            <div className="sidebar-section">
              <div className="section-title-row">
                <MapPin size={16} className="section-icon" />
                <h4>2. Puntos de Interés (POIs)</h4>
              </div>

              {/* Búsqueda por Dirección Física */}
              <form onSubmit={handleBuscarDireccionPOI} className="address-search-box">
                <label className="input-label-sm">Buscar por Dirección en {ciudadSeleccionada.nombre}:</label>
                <div className="address-input-row">
                  <input
                    type="text"
                    placeholder="Ej. Calle Manuela Velasco 80"
                    value={busquedaDireccionText}
                    onChange={(e) => setBusquedaDireccionText(e.target.value)}
                  />
                  <button type="submit" disabled={buscandoDireccion} className="btn-search-addr" title="Buscar dirección en Bolivia">
                    {buscandoDireccion ? '...' : <Search size={14} />}
                  </button>
                </div>
                {direccionStatus && (
                  <div className={`status-banner ${direccionStatus.success ? 'success' : 'error'}`}>
                    {direccionStatus.success ? <CheckCircle size={13} /> : <AlertCircle size={13} />}
                    <span>{direccionStatus.message}</span>
                  </div>
                )}
              </form>

              {/* Agregar POI manual */}
              <div className="add-poi-form">
                <label className="input-label-sm">O marcar punto manual en mapa:</label>
                <input
                  type="text"
                  placeholder="Nombre de referencia..."
                  value={nuevoPoiNombre}
                  onChange={(e) => setNuevoPoiNombre(e.target.value)}
                />
                <select
                  value={nuevoPoiTipo.id}
                  onChange={(e) => {
                    const sel = POI_TIPOS.find((t) => t.id === e.target.value);
                    if (sel) setNuevoPoiTipo(sel);
                  }}
                >
                  {POI_TIPOS.map((tipo) => (
                    <option key={tipo.id} value={tipo.id}>
                      {tipo.label}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  className={`btn-add-poi ${modoSeleccionarPoiEnMapa ? 'active' : ''}`}
                  onClick={() => setModoSeleccionarPoiEnMapa(!modoSeleccionarPoiEnMapa)}
                >
                  <Plus size={14} />
                  <span>{modoSeleccionarPoiEnMapa ? 'Haz clic en el mapa...' : 'Seleccionar en Mapa'}</span>
                </button>
              </div>

              {/* Lista de POIs */}
              <div className="pois-list">
                {pois.map((poi) => (
                  <div key={poi.id} className="poi-chip-clean">
                    <span className="poi-name-text">{poi.nombre}</span>
                    <button onClick={() => handleEliminarPoi(poi.id)} title="Eliminar POI">
                      <X size={12} />
                    </button>
                  </div>
                ))}
                {pois.length === 0 && <p className="no-pois">Agrega direcciones o selecciona puntos en el mapa.</p>}
              </div>
            </div>

            {/* Filtros Complementarios */}
            <div className="sidebar-section">
              <div className="section-title-row">
                <SlidersHorizontal size={16} className="section-icon" />
                <h4>3. Filtros de Oferta</h4>
              </div>
              <div className="form-row-compact">
                <div>
                  <label>Oferta</label>
                  <select value={tipoOferta} onChange={(e) => setTipoOferta(e.target.value)}>
                    <option value="">Todas</option>
                    <option value="alquiler">Alquiler</option>
                    <option value="venta">Venta</option>
                    <option value="anticretico">Anticrético</option>
                  </select>
                </div>
                <div>
                  <label>Precio Máx</label>
                  <input
                    type="number"
                    placeholder="USD"
                    value={precioMax}
                    onChange={(e) => setPrecioMax(e.target.value)}
                  />
                </div>
              </div>
            </div>

            <button
              className="btn-calcular-ia-pro"
              onClick={handleBuscarConIA}
              disabled={loading}
            >
              <Sparkles size={18} />
              <span>{loading ? 'Analizando con IA...' : 'Calcular Recomendaciones con IA'}</span>
            </button>

            {errorMsg && <div className="error-banner">{errorMsg}</div>}
          </div>

          {/* Panel 2: Mapa Completo (Flex 1) */}
          <div className="busqueda-mapa-viewport-container">
            <div ref={mapRef} className="full-screen-map-canvas"></div>

            {/* Botón flotante naranja 'Eliminar Dibujo' estilo InfoCasas */}
            {poligonoPuntos.length >= 3 && !modoDibujo && (
              <div className="floating-infocasas-action">
                <button
                  type="button"
                  className="btn-infocasas-eliminar"
                  onClick={handleEliminarDibujo}
                >
                  <Trash2 size={16} />
                  <span>Eliminar Dibujo</span>
                </button>
              </div>
            )}

            {/* Banner flotante cuando está en modo dibujo libre */}
            {modoDibujo && (
              <div className="drawing-banner-floating">
                <Edit3 size={16} className="picking-icon-pulse" />
                <span>Haz clic en el mapa para trazar los vértices de tu zona de búsqueda personalizada</span>
                <button onClick={() => setModoDibujo(false)}>Finalizar Trazo</button>
              </div>
            )}

            {/* Banner flotante cuando está en modo selección de POI */}
            {modoSeleccionarPoiEnMapa && (
              <div className="picking-banner-floating">
                <MapPin size={16} className="picking-icon-pulse" />
                <span>Modo de marcado activo: haz clic en el mapa para situar tu punto de interés</span>
                <button onClick={() => setModoSeleccionarPoiEnMapa(false)}>Cancelar</button>
              </div>
            )}

            {/* Botón para colapsar/expandir el panel de resultados */}
            {resultados.length > 0 && (
              <button
                className="btn-toggle-results-panel"
                onClick={() => setPanelResultadosAbierto(!panelResultadosAbierto)}
              >
                {panelResultadosAbierto ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                <span>{panelResultadosAbierto ? 'Ocultar Resultados' : `Ver Resultados (${resultados.length})`}</span>
              </button>
            )}
          </div>

          {/* Panel 3: Resultados Colapsables / Lateral Derecho */}
          {panelResultadosAbierto && (
            <div className="busqueda-results-sidebar">
              <div className="results-sidebar-header">
                <div>
                  <h5>Propiedades Recomendadas ({resultados.length})</h5>
                  <span className="results-subtitle">Ordenado por Score de Conveniencia y Rutina</span>
                </div>
                <button
                  className="btn-close-results-sidebar"
                  onClick={() => setPanelResultadosAbierto(false)}
                >
                  <X size={16} />
                </button>
              </div>

              {resultados.length === 0 && !loading && (
                <div className="empty-results-pro">
                  <Building size={32} className="empty-svg" />
                  <p>Presiona <strong>"Calcular Recomendaciones con IA"</strong> para obtener las mejores opciones en esta zona.</p>
                </div>
              )}

              <div className="results-cards-scroll">
                {resultados.map((item) => {
                  const isSelected = propiedadSeleccionada?.inmueble_id === item.inmueble_id;
                  const scoreClass = item.score_conveniencia >= 80 ? 'high' : item.score_conveniencia >= 60 ? 'mid' : 'low';

                  return (
                    <div
                      key={item.inmueble_id}
                      className={`result-card-pro ${isSelected ? 'active' : ''}`}
                      onClick={() => {
                        setPropiedadSeleccionada(item);
                        if (mapInstanceRef.current) {
                          mapInstanceRef.current.flyTo([item.lat, item.lng], 15);
                        }
                      }}
                    >
                      <div className="card-top-pro">
                        <div className="card-img-container">
                          <img
                            src={item.imagen || 'https://via.placeholder.com/300x200?text=Inmueble'}
                            alt={item.titulo}
                          />
                          <span className={`score-badge-overlay ${scoreClass}`}>
                            {item.score_conveniencia} pts
                          </span>
                        </div>
                        <div className="card-body-info">
                          <h6>{item.titulo}</h6>
                          <p className="card-dir-text">
                            <MapPin size={12} />
                            <span>{item.direccion}</span>
                          </p>
                          <div className="card-price-row">
                            <span className="price-bold">
                              {item.precio ? `$${item.precio} USD` : 'Consultar'}
                            </span>
                            <span className="tipo-badge">{item.tipo_oferta}</span>
                          </div>
                        </div>
                      </div>

                      {/* Score de Rutina Diaria & Ahorro de Tiempo */}
                      {item.ahorro_rutina_min && (
                        <div className="daily-routine-badge">
                          <Clock size={13} />
                          <span>Ahorro diario: <strong>~{item.ahorro_rutina_min} min/día</strong> en traslados</span>
                        </div>
                      )}

                      {/* Desglose de distancias a POIs */}
                      {item.desglose_pois && item.desglose_pois.length > 0 && (
                        <div className="card-pois-breakdown-pro">
                          <span className="breakdown-label">Desglose a tus POIs:</span>
                          <div className="poi-chips-grid">
                            {item.desglose_pois.map((poi, idx) => (
                              <div key={idx} className="poi-distance-tag">
                                <span className="poi-tag-name">{poi.nombre}:</span>
                                <strong>{poi.distancia_km} km</strong>
                                <span className="time-sub">
                                  (<Car size={11} /> {poi.minutos_auto} min)
                                </span>
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Justificación IA Ejecutiva */}
                      {item.justificacion_ia && (
                        <div className="ai-eval-box">
                          <div className="ai-eval-header">
                            <Sparkles size={13} />
                            <span>Análisis Ejecutivo IA (Groq):</span>
                          </div>
                          <p>{item.justificacion_ia}</p>
                        </div>
                      )}

                      {onSelectPropiedad && (
                        <button
                          className="btn-select-prop-pro"
                          onClick={(e) => {
                            e.stopPropagation();
                            onSelectPropiedad(item.inmueble_id);
                          }}
                        >
                          <span>Ver Ficha Completa</span>
                          <ChevronRight size={14} />
                        </button>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>,
    document.body
  );
}
