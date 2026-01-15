import { Shield, User } from 'lucide-react';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';

export function Header() {
  return (
    <header className="bg-primary text-primary-foreground shadow-md">
      <div className="container mx-auto px-4 py-3">
        <div className="flex items-center justify-between">
          {/* Logo and Title */}
          <div className="flex items-center gap-3">
            <div className="flex items-center justify-center w-10 h-10 bg-primary-foreground/10 rounded-lg">
              <Shield className="w-6 h-6 text-[#00A65E]" />
            </div>
            <div>
              <h1 className="text-lg font-semibold tracking-tight">Desafio Participa DF – Conectando Governo e Cidadão</h1>
              <p className="text-xs text-primary-foreground/70">Categoria Acesso à Informação: Módulo de Identificação de Dados Pessoais</p>
            </div>
          </div>

          {/* User Avatar */}
          <div className="flex items-center gap-3">
            <div className="hidden sm:block text-right">
              <p className="text-sm font-medium">Servidor</p>
              <p className="text-xs text-primary-foreground/70">CGDF</p>
            </div>
            <Avatar className="h-9 w-9 border-2 border-primary-foreground/20">
              <AvatarFallback className="bg-primary-foreground/10 text-primary-foreground text-sm">
                <User className="w-4 h-4" />
              </AvatarFallback>
            </Avatar>
          </div>
        </div>
      </div>
    </header>
  );
}
