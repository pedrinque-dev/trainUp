/** Ícone (figura + seta) e wordmark. Em fundos escuros usa o ícone transparente + texto em CSS. */
export function LogoMark({ size = 36, className = "" }) {
  return <img src="/logo-icon.png" alt="" width={size} height={size} className={`object-contain ${className}`} style={{ height: size, width: "auto" }} />;
}

export function Wordmark({ dark = false, className = "" }) {
  return (
    <span className={`text-xl font-extrabold tracking-tight ${className}`}>
      <span className={dark ? "text-white" : "text-ink"}>Train</span><span className="text-grad">Up</span>
    </span>
  );
}

export function LogoFull({ className = "h-14" }) {
  return <img src="/logo.png" alt="TrainUp" className={`w-auto ${className}`} />;
}
