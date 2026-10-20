export const cop = (n) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n ?? 0)
export const porDia = (items = []) =>
  Object.entries(items.reduce((a, i) => ((a[i.numero_dia] ??= []).push(i), a), {})).sort((a, b) => a[0] - b[0])
export const MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre']
export const IDIOMAS = ['English', 'Français', 'Português', 'Deutsch', 'Italiano']
