import { BrazilianAtomIcon } from './BrazilianAtomIcon';

export function Header() {
  return (
    <header className="border-b border-gray-200 shadow-sm">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        
        {/* Logo com Ícone Átomo Brasileiro */}
        <div className="flex items-center gap-3">
          <BrazilianAtomIcon size={40} />
          <div>
            <h1 className="text-2xl font-bold text-[#1351B4]">
              Participa DF
            </h1>
            <p className="text-xs text-gray-600">
              Análise de Privacidade em LAI
            </p>
          </div>
        </div>

        {/* Menu Navigation */}
        {/* ...existing code... */}
      </div>
    </header>
  );
}
