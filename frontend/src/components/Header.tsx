import { Shield } from 'lucide-react';

export function Header() {
  return (
    <header className="bg-[#1351B4] border-b-4 border-[#00A65E] shadow-lg">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex items-center justify-between">
        
        {/* Logo Original */}
        <div className="flex items-center gap-2">
          <Shield className="w-8 h-8 text-white" />
          <div>
            <h1 className="text-2xl font-bold text-white">
              Participa DF
            </h1>
            <p className="text-xs text-blue-100">
              Transparência com Segurança
            </p>
          </div>
        </div>

        {/* Menu Navigation */}
        {/* ...existing code... */}
      </div>
    </header>
  );
}
