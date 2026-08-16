import { useState, useEffect, useMemo } from 'react';
import {
  DollarSign, TrendingUp, Calendar, ShieldCheck, Sparkles,
  Sliders, Download, Building, Percent, Clock
} from 'lucide-react';
import {
  ResponsiveContainer, AreaChart, Area, BarChart, Bar,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend
} from 'recharts';
import html2pdf from 'html2pdf.js';
import valuacionService from '../services/valuacionService';
import './SimuladorInversion.css';

/**
 * SimuladorInversion — Dashboard financiero interactivo de Valuación Automática (AVM)
 * y simulador paramétrico de rendimiento y flujo de caja a 10 años.
 *
 * @param {object} props
 * @param {number} props.inmuebleId - ID de la propiedad
 * @param {object} [props.valuacionInicial] - Valuación previa cargada
 * @param {number} [props.precioReferencia] - Precio de venta o valor de mercado inicial
 */
const SimuladorInversion = ({ inmuebleId, valuacionInicial = null, precioReferencia = 120000 }) => {
  const [valuacion, setValuacion] = useState(valuacionInicial);
  const [cargandoValuacion, setCargandoValuacion] = useState(!valuacionInicial && !!inmuebleId);
  const [exportando, setExportando] = useState(false);

  // Parámetros de simulación en tiempo real (Sliders)
  const [precioCompra, setPrecioCompra] = useState(
    valuacionInicial?.precio_venta_optimo || precioReferencia || 120000
  );
  const [alquilerMensual, setAlquilerMensual] = useState(
    valuacionInicial?.precio_alquiler_optimo || Math.round(precioCompra * 0.007) || 850
  );
  const [tasaOcupacion, setTasaOcupacion] = useState(95); // %
  const [gastosOperativosPct, setGastosOperativosPct] = useState(10); // %
  const [plusvaliaAnualPct, setPlusvaliaAnualPct] = useState(3.5); // %

  // Cargar valuación AVM si no se proporcionó inicialmente
  useEffect(() => {
    if (valuacionInicial) {
      setValuacion(valuacionInicial);
      if (valuacionInicial.precio_venta_optimo) {
        setPrecioCompra(Number(valuacionInicial.precio_venta_optimo));
      }
      if (valuacionInicial.precio_alquiler_optimo) {
        setAlquilerMensual(Number(valuacionInicial.precio_alquiler_optimo));
      }
      return;
    }

    if (!inmuebleId) return;

    setCargandoValuacion(true);
    valuacionService.getValuacionPorInmueble(inmuebleId)
      .then((data) => {
        setValuacion(data);
        if (data.precio_venta_optimo) setPrecioCompra(Number(data.precio_venta_optimo));
        if (data.precio_alquiler_optimo) setAlquilerMensual(Number(data.precio_alquiler_optimo));
      })
      .catch((err) => {
        console.error('Error cargando valuación AVM:', err);
      })
      .finally(() => setCargandoValuacion(false));
  }, [inmuebleId, valuacionInicial]);

  // Cálculos financieros reactivos
  const metricas = useMemo(() => {
    const mesesEfectivos = 12 * (tasaOcupacion / 100);
    const ingresoBrutoAnual = alquilerMensual * mesesEfectivos;
    const gastosAnuales = ingresoBrutoAnual * (gastosOperativosPct / 100);
    const ingresoNetoAnual = ingresoBrutoAnual - gastosAnuales;

    const roiAnual = precioCompra > 0 ? (ingresoNetoAnual / precioCompra) * 100 : 0;
    const capRate = roiAnual;
    const paybackAnos = ingresoNetoAnual > 0 ? (precioCompra / ingresoNetoAnual).toFixed(1) : 0;

    // Proyección a 10 años
    const proyeccion = [];
    let acumulado = 0;
    let valorActivo = precioCompra;

    for (let anio = 1; anio <= 10; anio++) {
      const ingresoAnio = ingresoBrutoAnual * Math.pow(1.025, anio - 1);
      const gastoAnio = ingresoAnio * (gastosOperativosPct / 100);
      const netoAnio = ingresoAnio - gastoAnio;
      acumulado += netoAnio;
      valorActivo = valorActivo * (1 + plusvaliaAnualPct / 100);

      proyeccion.push({
        anio: `Año ${anio}`,
        'Ingreso Bruto': Math.round(ingresoAnio),
        'Gastos': Math.round(gastoAnio),
        'Flujo Neto Anual': Math.round(netoAnio),
        'Flujo Acumulado': Math.round(acumulado),
        'Valor Propiedad': Math.round(valorActivo),
      });
    }

    return {
      ingresoBrutoAnual: Math.round(ingresoBrutoAnual),
      gastosAnuales: Math.round(gastosAnuales),
      ingresoNetoAnual: Math.round(ingresoNetoAnual),
      roiAnual: roiAnual.toFixed(2),
      capRate: capRate.toFixed(2),
      paybackAnos,
      retornoTotal10Anos: Math.round(acumulado),
      proyeccion,
    };
  }, [precioCompra, alquilerMensual, tasaOcupacion, gastosOperativosPct, plusvaliaAnualPct]);

  // Exportar reporte a PDF
  const handleExportarPDF = () => {
    const element = document.getElementById('simulador-pdf-export-container');
    if (!element) return;

    setExportando(true);
    const opt = {
      margin: [10, 10],
      filename: `Reporte_Valuacion_e_Inversion_${inmuebleId || 'Simulacion'}.pdf`,
      image: { type: 'jpeg', quality: 0.98 },
      html2canvas: { scale: 2, useCORS: true, logging: false },
      jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' },
    };

    html2pdf().set(opt).from(element).save().then(() => {
      setExportando(false);
    });
  };

  const formatUSD = (val) =>
    new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', maximumFractionDigits: 0 }).format(val);

  return (
    <div className="simulador-inversion-container" id="simulador-pdf-export-container">
      {/* ─── Encabezado y Acción de Exportar ─── */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 12 }}>
        <div>
          <h2 style={{ fontSize: '1.45rem', fontWeight: 800, margin: 0, color: 'var(--color-text)' }}>
            📊 Valuación Automática & Simulador de Inversión
          </h2>
          <p style={{ margin: '4px 0 0 0', color: 'var(--color-text-secondary)', fontSize: '0.88rem' }}>
            Estimación de mercado basada en modelo hedónico inmobiliario boliviano y proyecciones de rentabilidad.
          </p>
        </div>
        <button
          className="simulador-export-btn"
          onClick={handleExportarPDF}
          disabled={exportando}
        >
          <Download size={16} />
          {exportando ? 'Generando PDF...' : 'Descargar Informe PDF'}
        </button>
      </div>

      {/* ─── Tarjetas KPI Principales ─── */}
      <div className="simulador-kpis-grid">
        <div className="simulador-kpi-card">
          <div className="simulador-kpi-icon primary">
            <DollarSign size={24} />
          </div>
          <div className="simulador-kpi-content">
            <h4>Alquiler Sugerido</h4>
            <p className="simulador-kpi-value">{formatUSD(alquilerMensual)}/mes</p>
            <span className="simulador-kpi-sub">
              Rango: {formatUSD(valuacion?.precio_alquiler_min || alquilerMensual * 0.88)} - {formatUSD(valuacion?.precio_alquiler_max || alquilerMensual * 1.14)}
            </span>
          </div>
        </div>

        <div className="simulador-kpi-card">
          <div className="simulador-kpi-icon success">
            <TrendingUp size={24} />
          </div>
          <div className="simulador-kpi-content">
            <h4>Retorno Anual (ROI)</h4>
            <p className="simulador-kpi-value">{metricas.roiAnual}%</p>
            <span className="simulador-kpi-sub">Cap Rate estimado: {metricas.capRate}%</span>
          </div>
        </div>

        <div className="simulador-kpi-card">
          <div className="simulador-kpi-icon warning">
            <Clock size={24} />
          </div>
          <div className="simulador-kpi-content">
            <h4>Tiempo sin Inquilino</h4>
            <p className="simulador-kpi-value">{valuacion?.dias_vacancia_estimados || 14} días</p>
            <span className="simulador-kpi-sub">Vacancia anual ~ {100 - tasaOcupacion}%</span>
          </div>
        </div>

        <div className="simulador-kpi-card">
          <div className="simulador-kpi-icon info">
            <ShieldCheck size={24} />
          </div>
          <div className="simulador-kpi-content">
            <h4>Confianza del Modelo</h4>
            <p className="simulador-kpi-value">{valuacion?.confianza_porcentaje || 92}%</p>
            <span className="simulador-kpi-sub">Payback estimado: {metricas.paybackAnos} años</span>
          </div>
        </div>
      </div>

      {/* ─── Grid Principal: Controles Interactivos + Gráficos ─── */}
      <div className="simulador-main-grid">
        {/* Panel de Sliders Interactivos */}
        <div className="simulador-panel-sliders">
          <div className="simulador-panel-header">
            <h3 className="simulador-panel-title">
              <Sliders size={18} color="#0ea5e9" />
              Parámetros de Simulación
            </h3>
          </div>

          {/* Slider 1: Precio de Compra / Valor Activo */}
          <div className="simulador-slider-group">
            <div className="simulador-slider-label-row">
              <span>Valor del Inmueble</span>
              <span className="simulador-slider-val">{formatUSD(precioCompra)}</span>
            </div>
            <input
              type="range"
              min={30000}
              max={600000}
              step={2000}
              value={precioCompra}
              onChange={(e) => setPrecioCompra(Number(e.target.value))}
              className="simulador-range-input"
            />
          </div>

          {/* Slider 2: Alquiler Mensual Proyectado */}
          <div className="simulador-slider-group">
            <div className="simulador-slider-label-row">
              <span>Alquiler Mensual Estimado</span>
              <span className="simulador-slider-val">{formatUSD(alquilerMensual)}/mes</span>
            </div>
            <input
              type="range"
              min={200}
              max={4000}
              step={25}
              value={alquilerMensual}
              onChange={(e) => setAlquilerMensual(Number(e.target.value))}
              className="simulador-range-input"
            />
          </div>

          {/* Slider 3: Tasa de Ocupación Anual */}
          <div className="simulador-slider-group">
            <div className="simulador-slider-label-row">
              <span>Tasa de Ocupación Anual</span>
              <span className="simulador-slider-val">{tasaOcupacion}%</span>
            </div>
            <input
              type="range"
              min={70}
              max={100}
              step={1}
              value={tasaOcupacion}
              onChange={(e) => setTasaOcupacion(Number(e.target.value))}
              className="simulador-range-input"
            />
          </div>

          {/* Slider 4: Gastos Operativos & Mantenimiento */}
          <div className="simulador-slider-group">
            <div className="simulador-slider-label-row">
              <span>Gastos Operativos & Mantenimiento</span>
              <span className="simulador-slider-val">{gastosOperativosPct}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={30}
              step={1}
              value={gastosOperativosPct}
              onChange={(e) => setGastosOperativosPct(Number(e.target.value))}
              className="simulador-range-input"
            />
          </div>

          {/* Slider 5: Plusvalía Anual Estimada */}
          <div className="simulador-slider-group">
            <div className="simulador-slider-label-row">
              <span>Plusvalía Anual Estimada</span>
              <span className="simulador-slider-val">{plusvaliaAnualPct}%</span>
            </div>
            <input
              type="range"
              min={0}
              max={10}
              step={0.5}
              value={plusvaliaAnualPct}
              onChange={(e) => setPlusvaliaAnualPct(Number(e.target.value))}
              className="simulador-range-input"
            />
          </div>

          {/* Resumen Financiero Anual */}
          <div style={{ marginTop: 'auto', padding: '16px', background: 'rgba(14, 165, 233, 0.05)', borderRadius: '12px', border: '1px solid rgba(14, 165, 233, 0.15)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.86rem' }}>
              <span>Ingreso Bruto Anual:</span>
              <strong>{formatUSD(metricas.ingresoBrutoAnual)}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.86rem', color: '#dc2626' }}>
              <span>Gastos Operativos Anuales:</span>
              <strong>-{formatUSD(metricas.gastosAnuales)}</strong>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', paddingTop: 8, borderTop: '1px solid rgba(14, 165, 233, 0.2)', fontSize: '0.95rem', color: '#059669', fontWeight: 800 }}>
              <span>Flujo Neto Anual (Cash Flow):</span>
              <strong>{formatUSD(metricas.ingresoNetoAnual)}</strong>
            </div>
          </div>
        </div>

        {/* Panel de Gráfico Recharts de Proyección 10 Años */}
        <div className="simulador-panel-charts">
          <h3 className="simulador-panel-title">
            <TrendingUp size={18} color="#059669" />
            Proyección de Flujo de Caja Acumulado (10 Años)
          </h3>
          <div style={{ width: '100%', height: 320, minWidth: 0, minHeight: 320, position: 'relative' }}>
            <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={280}>
              <AreaChart data={metricas.proyeccion} margin={{ top: 10, right: 10, left: 0, bottom: 0 }}>
                <defs>
                  <linearGradient id="colorFlujo" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#0ea5e9" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#0ea5e9" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="colorNeto" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#10b981" stopOpacity={0.4} />
                    <stop offset="95%" stopColor="#10b981" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#e2e8f0" />
                <XAxis dataKey="anio" stroke="#64748b" fontSize={12} />
                <YAxis stroke="#64748b" fontSize={12} tickFormatter={(val) => `$${val / 1000}k`} />
                <Tooltip
                  formatter={(val) => [`$${val.toLocaleString()}`, '']}
                  contentStyle={{ background: '#1e293b', border: 'none', borderRadius: '8px', color: '#f8fafc' }}
                />
                <Legend />
                <Area type="monotone" dataKey="Flujo Acumulado" stroke="#0ea5e9" strokeWidth={2} fillOpacity={1} fill="url(#colorFlujo)" />
                <Area type="monotone" dataKey="Flujo Neto Anual" stroke="#10b981" strokeWidth={2} fillOpacity={1} fill="url(#colorNeto)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>

      {/* ─── Diagnóstico de Mercado con IA ─── */}
      <div className="simulador-ai-diagnostic">
        <div className="simulador-ai-header">
          <Sparkles size={18} />
          Diagnóstico de Mercado & Recomendaciones Estratégicas (IA Groq)
        </div>
        <p className="simulador-ai-text">
          {valuacion?.analisis_mercado_ia || (
            `La propiedad presenta un precio sugerido óptimo de alquiler de ${formatUSD(alquilerMensual)}/mes con una tasa de retorno anual (ROI) estimada de ${metricas.roiAnual}%. Se recomienda mantener la propiedad amoblada para reducir el período de vacancia a menos de 15 días y maximizar el flujo de caja neto.`
          )}
        </p>
      </div>

      {/* ─── Tabla de Propiedades Comparables en la Zona ─── */}
      {valuacion?.comparables && valuacion.comparables.length > 0 && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <h3 style={{ fontSize: '1.1rem', fontWeight: 700, margin: 0, color: 'var(--color-text)' }}>
            📍 Inmuebles Comparables en la Misma Zona
          </h3>
          <div className="simulador-comparables-table-wrapper">
            <table className="simulador-comparables-table">
              <thead>
                <tr>
                  <th>Propiedad</th>
                  <th>Zona / Ciudad</th>
                  <th>Superficie</th>
                  <th>Habitaciones</th>
                  <th>Precio Oferta</th>
                  <th>Precio / m²</th>
                </tr>
              </thead>
              <tbody>
                {valuacion.comparables.map((comp, idx) => (
                  <tr key={idx}>
                    <td style={{ fontWeight: 600 }}>{comp.titulo}</td>
                    <td>{comp.zona}</td>
                    <td>{comp.superficie} m²</td>
                    <td>{comp.habitaciones} dorms</td>
                    <td style={{ fontWeight: 700, color: '#4f46e5' }}>${comp.precio_oferta} {comp.tipo_oferta}</td>
                    <td>${comp.precio_m2}/m²</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};

export default SimuladorInversion;
