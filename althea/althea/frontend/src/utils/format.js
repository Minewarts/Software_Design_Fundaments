export const cop = (n) =>
  new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', maximumFractionDigits: 0 }).format(n ?? 0)
export const porDia = (items = []) =>
  Object.entries(items.reduce((a, i) => ((a[i.numero_dia] ??= []).push(i), a), {})).sort((a, b) => a[0] - b[0])
