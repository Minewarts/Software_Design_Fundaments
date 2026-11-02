const TOAST_EVENT = 'althea:toast'

export function mostrarToast(mensaje, tipo = 'success') {
  if (typeof window === 'undefined') return
  window.dispatchEvent(new CustomEvent(TOAST_EVENT, {
    detail: { mensaje, tipo },
  }))
}

export { TOAST_EVENT }
