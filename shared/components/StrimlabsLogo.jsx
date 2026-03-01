export function StrimlabsIcon({ size = 32, id = "sl" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none">
      <defs>
        <linearGradient id={`${id}-g`} x1="0%" y1="0%" x2="100%" y2="100%">
          <stop offset="0%"   stopColor="#8B2BE2"/>
          <stop offset="100%" stopColor="#00E5FF"/>
        </linearGradient>
      </defs>
      <circle cx="50" cy="50" r="42" stroke={`url(#${id}-g)`} strokeWidth="5" fill="rgba(139,43,226,0.1)"/>
      <path d="M38 32 L38 68 L72 50 Z" fill={`url(#${id}-g)`}/>
      <path d="M76 38 Q84 50 76 62" stroke={`url(#${id}-g)`} strokeWidth="4" fill="none" strokeLinecap="round"/>
      <path d="M82 32 Q94 50 82 68" stroke={`url(#${id}-g)`} strokeWidth="3" fill="none" strokeLinecap="round" opacity=".5"/>
    </svg>
  );
}

export function StrimlabsWordmark({ height = 28 }) {
  return (
    <div style={{ display:"flex", alignItems:"center", gap:10 }}>
      <StrimlabsIcon size={height} id="wm"/>
      <span style={{
        fontFamily:"'Space Mono',monospace", fontWeight:800, fontSize:height * 0.6,
        background:"linear-gradient(90deg,#8B2BE2,#00E5FF)",
        WebkitBackgroundClip:"text", WebkitTextFillColor:"transparent",
      }}>STRIMLABS</span>
    </div>
  );
}

export default StrimlabsWordmark;
