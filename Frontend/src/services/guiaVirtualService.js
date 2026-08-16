import api from './api';

/**
 * Servicio para interactuar con la Guía Virtual con Voz 3D y asistencia Q&A en tiempo real.
 */
const guiaVirtualService = {
  /**
   * Obtiene la narración espacial en tiempo real para una habitación activa.
   * @param {number} inmuebleId 
   * @param {string} habitacion 
   * @param {object} orientacion {pitch, yaw}
   */
  narrar: async (inmuebleId, habitacion, orientacion = {}) => {
    const response = await api.post('/inmuebles/guia-virtual/narrar/', {
      inmueble_id: inmuebleId,
      habitacion,
      orientacion,
    });
    return response.data?.data || response.data;
  },

  /**
   * Envía una consulta por voz/texto a la IA sobre la propiedad.
   * @param {number} inmuebleId 
   * @param {string} pregunta 
   * @param {string} habitacionActual 
   */
  consultar: async (inmuebleId, pregunta, habitacionActual = '') => {
    const response = await api.post('/inmuebles/guia-virtual/consultar/', {
      inmueble_id: inmuebleId,
      pregunta,
      habitacion_actual: habitacionActual,
    });
    return response.data?.data || response.data;
  },

  /**
   * Agenda una visita presencial directamente desde la guía virtual 3D.
   * @param {number} inmuebleId 
   * @param {string} fecha YYYY-MM-DD
   * @param {string} horaInicio HH:MM
   * @param {string} horaFin HH:MM
   * @param {string} notas 
   */
  agendar: async (inmuebleId, fecha, horaInicio, horaFin = '', notas = '') => {
    const response = await api.post('/inmuebles/guia-virtual/agendar/', {
      inmueble_id: inmuebleId,
      fecha,
      hora_inicio: horaInicio,
      hora_fin: horaFin,
      notas,
    });
    return response.data?.data || response.data;
  },
};

export default guiaVirtualService;
