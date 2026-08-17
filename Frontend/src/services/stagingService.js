import api from './api';

/**
 * Servicio para gestionar versiones amobladas virtualmente con IA (Virtual Staging 360° y 2D).
 */
const stagingService = {
  /**
   * Obtiene todos los amoblados virtuales de un inmueble.
   * @param {number} inmuebleId 
   * @param {string} [tipo] 'foto_2d' | 'panorama360'
   */
  getByInmueble: async (inmuebleId, tipo = null) => {
    const params = { inmueble: inmuebleId };
    if (tipo) params.tipo = tipo;
    const response = await api.get('/inmuebles/amoblados/', { params });
    return response.data?.results || response.data || [];
  },

  /**
   * Genera una nueva versión amoblada con IA (Google Gemini AI Studio).
   * Acepta { inmueble_id, multimedia_id, estilo, ambiente, prompt, tipo, imagen, guardar_en_inmueble }
   */
  generarAmoblado: async (paramsOrId, multimediaId = null, estilo = 'moderno', tipo = 'foto_2d', prompt = '', ambiente = 'sala') => {
    let payload = {};
    if (typeof paramsOrId === 'object' && paramsOrId !== null) {
      payload = {
        inmueble_id: paramsOrId.inmueble_id || paramsOrId.inmuebleId || paramsOrId.inmueble,
        multimedia_id: paramsOrId.multimedia_id || paramsOrId.multimediaId || null,
        estilo: paramsOrId.estilo || 'moderno',
        ambiente: paramsOrId.ambiente || 'sala',
        prompt: paramsOrId.prompt || '',
        tipo: paramsOrId.tipo || 'foto_2d',
        imagen: paramsOrId.imagen || null,
        guardar_en_inmueble: paramsOrId.guardar_en_inmueble || false,
      };
    } else {
      payload = {
        inmueble_id: paramsOrId,
        multimedia_id: multimediaId,
        estilo,
        ambiente,
        prompt,
        tipo,
      };
    }

    // Si viene una imagen (File o Blob), enviar como FormData
    if (payload.imagen instanceof File || payload.imagen instanceof Blob) {
      const formData = new FormData();
      formData.append('inmueble_id', payload.inmueble_id);
      if (payload.multimedia_id) formData.append('multimedia_id', payload.multimedia_id);
      formData.append('estilo', payload.estilo);
      formData.append('ambiente', payload.ambiente);
      if (payload.prompt) formData.append('prompt', payload.prompt);
      formData.append('tipo', payload.tipo);
      formData.append('imagen', payload.imagen);
      formData.append('guardar_en_inmueble', payload.guardar_en_inmueble ? 'true' : 'false');

      const response = await api.post('/inmuebles/amoblados/generar/', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
      });
      return response.data?.data || response.data;
    }

    const response = await api.post('/inmuebles/amoblados/generar/', payload);
    return response.data?.data || response.data;
  },

  /**
   * Alias de generarAmoblado para compatibilidad
   */
  generar: async (...args) => {
    return stagingService.generarAmoblado(...args);
  },

  /**
   * Asigna o actualiza el ambiente de una foto multimedia existente.
   */
  asignarAmbiente: async (multimediaId, ambiente) => {
    const response = await api.patch(`/inmuebles/multimedia/${multimediaId}/asignar-ambiente/`, { ambiente });
    return response.data?.data || response.data;
  },
};

export default stagingService;
