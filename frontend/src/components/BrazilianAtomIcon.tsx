/**
 * Ícone Átomo Brasileiro
 * Núcleo azul (Gov.br) com órbitas nas cores da bandeira
 */

interface BrazilianAtomIconProps {
  size?: number;
  className?: string;
}

export function BrazilianAtomIcon({ size = 40, className = "" }: BrazilianAtomIconProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 100 100"
      className={className}
      xmlns="http://www.w3.org/2000/svg"
    >
      {/* Órbita Verde (Brasil) */}
      <circle
        cx="50"
        cy="50"
        r="35"
        fill="none"
        stroke="#00A65E"
        strokeWidth="1.5"
        opacity="0.6"
      />

      {/* Órbita Amarela */}
      <circle
        cx="50"
        cy="50"
        r="24"
        fill="none"
        stroke="#FDB700"
        strokeWidth="1.5"
        opacity="0.6"
      />

      {/* Núcleo Azul (Gov.br) */}
      <circle
        cx="50"
        cy="50"
        r="12"
        fill="#1351B4"
      />

      {/* Elétron 1 (Verde) - posição 0° */}
      <circle
        cx="50"
        cy="15"
        r="3.5"
        fill="#00A65E"
      />

      {/* Elétron 2 (Amarelo) - posição 120° */}
      <circle
        cx="80.6"
        cy="62.5"
        r="3.5"
        fill="#FDB700"
      />

      {/* Elétron 3 (Vermelho) - posição 240° */}
      <circle
        cx="19.4"
        cy="62.5"
        r="3.5"
        fill="#E60000"
      />
    </svg>
  );
}
