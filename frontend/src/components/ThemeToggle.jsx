// Botón de la topbar para alternar entre tema oscuro (default) y claro.
// El estado real vive en App.jsx (persistido en localStorage); este componente
// solo dibuja el ícono correcto y dispara el cambio.
// `tema` usa los mismos valores que el atributo data-theme del CSS ('dark' | 'light'),
// para que no haya que traducir entre estado de React y selector de CSS en dos lugares.

import { Sun, Moon } from 'lucide-react'

export function ThemeToggle({ tema, onCambiar }) {
  const esOscuro = tema === 'dark'
  return (
    <button
      className="theme-toggle"
      onClick={onCambiar}
      aria-label={esOscuro ? 'Cambiar a tema claro' : 'Cambiar a tema oscuro'}
      title={esOscuro ? 'Tema claro' : 'Tema oscuro'}
    >
      {esOscuro ? <Moon size={15} /> : <Sun size={15} />}
    </button>
  )
}
