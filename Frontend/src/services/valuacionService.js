import api from './api';

/**
 * Servicio para interactuar con la Valuación Automática (AVM) y el Simulador Financiero de Inversión.
 */
const valuacionService = {
  /**
   * Obtiene la valuación de mercado guardada de un inmueble (o la calcula si no existe).
   * @param {number} inmuebleId 
   */
  getValuacionPorInmueble: async (inmuebleId) => {
    const response = await api.get('/inmuebles/valuaciones/por-inmueble/', {
      params: { inmueble_id: inmuebleId },
    });
    return response.data?.data || response.data;
  },

  /**
   * Fuerza el recálculo analítico del modelo hedónico y diagnóstico Groq.
   * @param {number} inmuebleId 
   */
  calcularValuacion: async (inmuebleId) => {
    const response = await api.post('/inmuebles/valuaciones/calcular/', {
      inmueble_id: inmuebleId,
    });
    return response.data?.data || response.data;
  },

  /**
   * Ejecuta una simulación financiera paramétrica en tiempo real (Cash Flow 10 años, ROI, Cap Rate).
   * @param {object} params
   * @param {number} [params.inmueble_id]
   * @param {number} params.precio_compra
   * @param {number} params.alquiler_mensual
   * @param {number} params.tasa_ocupacion
   * @param {number} params.gastos_operativos_pct
   * @param {number} params.plusvalia_anual_pct
   */
  simularInversion: async (params) => {
    const response = await api.post('/inmuebles/valuaciones/simular/', params);
    return response.data?.data || response.data;
  },
};

export default valuacionService;
