import os
import subprocess
from PIL import Image

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BRAND_DIR = os.path.join(REPO_ROOT, "custom_components", "sprsun_modbus", "brand")
IMAGES_DIR = os.path.join(REPO_ROOT, "images")
os.makedirs(BRAND_DIR, exist_ok=True)
os.makedirs(IMAGES_DIR, exist_ok=True)

def get_icon_svg(is_dark=False):
    bg_grad_1 = "#0c1626" if not is_dark else "#060d18"
    bg_grad_2 = "#060c16" if not is_dark else "#03070d"
    border_col = "#2563EB" if not is_dark else "#38BDF8"
    border_opacity = "0.45" if not is_dark else "0.65"
    blade_hi = "#64748B" if not is_dark else "#788CA5"
    blade_lo = "#1E293B" if not is_dark else "#152030"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <!-- Background Chassis Gradient -->
    <linearGradient id="chassisGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="{bg_grad_1}" />
      <stop offset="100%" stop-color="{bg_grad_2}" />
    </linearGradient>

    <!-- Warm Heating Arc Gradient -->
    <linearGradient id="warmArc" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#EF4444" />
      <stop offset="50%" stop-color="#F97316" />
      <stop offset="100%" stop-color="#FBBF24" />
    </linearGradient>

    <!-- Cool Cooling Arc Gradient -->
    <linearGradient id="coolArc" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284C7" />
      <stop offset="50%" stop-color="#0EA5E9" />
      <stop offset="100%" stop-color="#38BDF8" />
    </linearGradient>

    <!-- Fan Blade Gradient -->
    <linearGradient id="bladeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="{blade_hi}" />
      <stop offset="100%" stop-color="{blade_lo}" />
    </linearGradient>

    <!-- Metallic Hub -->
    <radialGradient id="hubGrad" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#94A3B8" />
      <stop offset="50%" stop-color="#475569" />
      <stop offset="100%" stop-color="#0F172A" />
    </radialGradient>

    <!-- Filters -->
    <filter id="shadowIcon" x="-10%" y="-10%" width="125%" height="125%">
      <feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#000000" flood-opacity="0.6"/>
    </filter>
    <filter id="glowArc" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
    <filter id="ledGlow" x="-50%" y="-50%" width="200%" height="200%">
      <feGaussianBlur stdDeviation="3" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Outer Squircle: Heat Pump Outdoor Chassis -->
  <rect x="16" y="16" width="480" height="480" rx="108" fill="url(#chassisGrad)" stroke="{border_col}" stroke-width="4" stroke-opacity="{border_opacity}" filter="url(#shadowIcon)" />

  <!-- Top Bevel Highlight Line -->
  <path d="M 124 20 L 388 20" stroke="#38BDF8" stroke-width="2" stroke-opacity="0.4" stroke-linecap="round"/>

  <!-- Top Header Section: SPRSUN Brand + LCD Screen -->
  <g transform="translate(56, 56)">
    <text x="0" y="38" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="36" font-weight="900" fill="#FFFFFF" letter-spacing="4">SPRSUN</text>
  </g>

  <!-- Digital Temperature & Modbus Status LCD Display -->
  <g transform="translate(340, 64)">
    <rect x="0" y="0" width="116" height="42" rx="10" fill="#03070F" stroke="#1E2E44" stroke-width="2"/>
    <circle cx="20" cy="21" r="5" fill="#10B981" filter="url(#ledGlow)"/>
    <circle cx="20" cy="21" r="2.5" fill="#A7F3D0"/>
    <text x="40" y="28" font-family="monospace, monospace" font-size="18" font-weight="bold" fill="#38BDF8" letter-spacing="1">48°C</text>
  </g>

  <!-- Horizontal Divider Line -->
  <line x1="48" y1="128" x2="464" y2="128" stroke="#1E2E44" stroke-width="2" stroke-opacity="0.6"/>

  <!-- Center Section: Axial Fan & Thermal Aura -->
  <!-- Thermal Flow Ribbons -->
  <!-- Warm Heating Arc (Top-Right) -->
  <path d="M 256 150 A 136 136 0 0 1 392 286" fill="none" stroke="url(#warmArc)" stroke-width="14" stroke-linecap="round" opacity="0.95" filter="url(#glowArc)" />
  <!-- Cool Cooling Arc (Bottom-Left) -->
  <path d="M 256 422 A 136 136 0 0 1 120 286" fill="none" stroke="url(#coolArc)" stroke-width="14" stroke-linecap="round" opacity="0.95" filter="url(#glowArc)" />

  <!-- Fan Outer Housing Bezel -->
  <circle cx="256" cy="286" r="118" fill="#040810" stroke="#1E334D" stroke-width="5" />
  
  <!-- Concentric Grille Rings -->
  <circle cx="256" cy="286" r="102" fill="none" stroke="#162538" stroke-width="2.5" />
  <circle cx="256" cy="286" r="80" fill="none" stroke="#162538" stroke-width="2" />
  <circle cx="256" cy="286" r="56" fill="none" stroke="#162538" stroke-width="1.8" />

  <!-- Radial Spoke Bars -->
  <g stroke="#142232" stroke-width="2.5">
    <line x1="256" y1="170" x2="256" y2="402" />
    <line x1="140" y1="286" x2="372" y2="286" />
    <line x1="174" y1="204" x2="338" y2="368" />
    <line x1="174" y1="368" x2="338" y2="204" />
  </g>

  <!-- 4 Aerodynamic Fan Blades -->
  <g transform="rotate(28, 256, 286)">
    <!-- Blade 1 (North) -->
    <path d="M 256 266 C 242 220 220 188 252 172 C 272 188 270 232 256 266 Z" fill="url(#bladeGrad)" stroke="#475569" stroke-width="1.5"/>
    <path d="M 252 176 C 266 190 264 228 254 258" stroke="#94A3B8" stroke-width="1.5" fill="none" opacity="0.6"/>

    <!-- Blade 2 (East) -->
    <path d="M 276 286 C 322 272 354 250 370 282 C 354 302 310 300 276 286 Z" fill="url(#bladeGrad)" stroke="#475569" stroke-width="1.5"/>
    <path d="M 366 278 C 352 292 314 290 284 284" stroke="#94A3B8" stroke-width="1.5" fill="none" opacity="0.6"/>

    <!-- Blade 3 (South) -->
    <path d="M 256 306 C 270 352 292 384 260 400 C 240 384 242 340 256 306 Z" fill="url(#bladeGrad)" stroke="#475569" stroke-width="1.5"/>
    <path d="M 260 396 C 246 382 248 344 258 314" stroke="#94A3B8" stroke-width="1.5" fill="none" opacity="0.6"/>

    <!-- Blade 4 (West) -->
    <path d="M 236 286 C 190 300 158 322 142 290 C 158 270 202 272 236 286 Z" fill="url(#bladeGrad)" stroke="#475569" stroke-width="1.5"/>
    <path d="M 146 294 C 160 280 198 282 228 288" stroke="#94A3B8" stroke-width="1.5" fill="none" opacity="0.6"/>
  </g>

  <!-- Central Metal Hub -->
  <circle cx="256" cy="286" r="32" fill="url(#hubGrad)" stroke="#64748B" stroke-width="3" />
  <circle cx="251" cy="286" r="6" fill="#EF4444" filter="url(#ledGlow)"/>
  <circle cx="261" cy="286" r="6" fill="#0EA5E9" filter="url(#ledGlow)"/>

  <!-- Bottom Section: Modbus Connectivity Badge Pill -->
  <g transform="translate(136, 436)">
    <rect x="0" y="0" width="240" height="38" rx="19" fill="#050C16" stroke="#1E334D" stroke-width="2"/>
    <circle cx="26" cy="19" r="5" fill="#10B981" filter="url(#ledGlow)"/>
    <line x1="31" y1="19" x2="45" y2="19" stroke="#10B981" stroke-width="2"/>
    <circle cx="47" cy="19" r="4" fill="#38BDF8"/>
    <line x1="51" y1="19" x2="63" y2="19" stroke="#38BDF8" stroke-width="2"/>
    <circle cx="65" cy="19" r="4.5" fill="#F59E0B"/>
    <text x="80" y="25" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="14" font-weight="900" fill="#E2E8F0" letter-spacing="3.5">MODBUS</text>
  </g>
</svg>'''
    return svg

def get_logo_svg(is_dark=False):
    # Canvas 680 x 200, transparent background
    brand_grad_start = "#0066CC" if not is_dark else "#38BDF8"
    brand_grad_end = "#0284C7" if not is_dark else "#60A5FA"
    title_sub_color = "#1E293B" if not is_dark else "#F1F5F9"
    badge_bg = "#F1F5F9" if not is_dark else "#0F172A"
    badge_stroke = "#CBD5E1" if not is_dark else "#1E293B"
    badge_text = "#475569" if not is_dark else "#94A3B8"
    modbus_bg = "#E0F2FE" if not is_dark else "#0C2340"
    modbus_stroke = "#38BDF8" if not is_dark else "#0284C7"
    modbus_text = "#0284C7" if not is_dark else "#38BDF8"

    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 680 200" width="680" height="200">
  <defs>
    <linearGradient id="logoBrandGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="{brand_grad_start}" />
      <stop offset="100%" stop-color="{brand_grad_end}" />
    </linearGradient>
    <linearGradient id="warmLogoArc" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#EF4444" />
      <stop offset="50%" stop-color="#F97316" />
      <stop offset="100%" stop-color="#FBBF24" />
    </linearGradient>
    <linearGradient id="coolLogoArc" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284C7" />
      <stop offset="50%" stop-color="#0EA5E9" />
      <stop offset="100%" stop-color="#38BDF8" />
    </linearGradient>
    <linearGradient id="bladeGradLogo" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#64748B" />
      <stop offset="100%" stop-color="#1E293B" />
    </linearGradient>
    <radialGradient id="hubGradLogo" cx="35%" cy="35%" r="65%">
      <stop offset="0%" stop-color="#94A3B8" />
      <stop offset="100%" stop-color="#1E293B" />
    </radialGradient>
    <filter id="glowLogo" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="4" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Left Icon Emblem (Squircle 160x160 at x=20, y=20) -->
  <g transform="translate(20, 20)">
    <rect x="0" y="0" width="160" height="160" rx="38" fill="#0C1626" stroke="#2563EB" stroke-width="2.5" stroke-opacity="0.6"/>
    
    <!-- Thermal Arcs -->
    <path d="M 80 26 A 54 54 0 0 1 134 80" fill="none" stroke="url(#warmLogoArc)" stroke-width="7" stroke-linecap="round" filter="url(#glowLogo)" />
    <path d="M 80 134 A 54 54 0 0 1 26 80" fill="none" stroke="url(#coolLogoArc)" stroke-width="7" stroke-linecap="round" filter="url(#glowLogo)" />

    <!-- Fan Outer Housing -->
    <circle cx="80" cy="80" r="46" fill="#040810" stroke="#1E334D" stroke-width="2.5" />
    <circle cx="80" cy="80" r="34" fill="none" stroke="#162538" stroke-width="1.5" />

    <!-- Fan Blades -->
    <g transform="rotate(28, 80, 80)">
      <path d="M 80 72 C 74 54 66 42 78 35 C 86 42 86 60 80 72 Z" fill="url(#bladeGradLogo)" stroke="#475569" stroke-width="1"/>
      <path d="M 88 80 C 106 74 118 66 125 78 C 118 86 100 86 88 80 Z" fill="url(#bladeGradLogo)" stroke="#475569" stroke-width="1"/>
      <path d="M 80 88 C 86 106 94 118 82 125 C 74 118 74 100 80 88 Z" fill="url(#bladeGradLogo)" stroke="#475569" stroke-width="1"/>
      <path d="M 72 80 C 54 86 42 94 35 82 C 42 74 60 74 72 80 Z" fill="url(#bladeGradLogo)" stroke="#475569" stroke-width="1"/>
    </g>

    <!-- Hub -->
    <circle cx="80" cy="80" r="14" fill="url(#hubGradLogo)" stroke="#64748B" stroke-width="1.8" />
    <circle cx="78" cy="80" r="3" fill="#EF4444" />
    <circle cx="82" cy="80" r="3" fill="#0EA5E9" />
  </g>

  <!-- Right Typography Section -->
  <g transform="translate(205, 0)">
    <!-- Brand Title: SPRSUN -->
    <text x="0" y="80" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="52" font-weight="900" fill="url(#logoBrandGrad)" letter-spacing="3.5">SPRSUN</text>
    
    <!-- Heat Pump Subtitle -->
    <text x="4" y="116" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="20" font-weight="800" fill="{title_sub_color}" letter-spacing="4.5">HEAT PUMP</text>
    
    <!-- Thin accent divider -->
    <line x1="4" y1="128" x2="440" y2="128" stroke="#38BDF8" stroke-width="2" stroke-opacity="0.3" />

    <!-- Badges Row -->
    <!-- Modbus Pill -->
    <rect x="4" y="142" width="134" height="32" rx="8" fill="{modbus_bg}" stroke="{modbus_stroke}" stroke-width="1.5" />
    <circle cx="22" cy="158" r="4.5" fill="#10B981" />
    <text x="35" y="163" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="12" font-weight="bold" fill="{modbus_text}" letter-spacing="1.5">MODBUS</text>

    <!-- Home Assistant Badge -->
    <rect x="150" y="142" width="176" height="32" rx="8" fill="{badge_bg}" stroke="{badge_stroke}" stroke-width="1.5" />
    <text x="164" y="163" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="12" font-weight="700" fill="{badge_text}" letter-spacing="1">HOME ASSISTANT</text>
  </g>
</svg>'''
    return svg

def get_banner_svg():
    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1280 420" width="1280" height="420">
  <defs>
    <!-- Background Gradient -->
    <linearGradient id="banBg" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#060C16" />
      <stop offset="50%" stop-color="#0A1526" />
      <stop offset="100%" stop-color="#040810" />
    </linearGradient>

    <!-- Ambient Glows -->
    <radialGradient id="blueGlow" cx="20%" cy="50%" r="50%">
      <stop offset="0%" stop-color="#1D4ED8" stop-opacity="0.35" />
      <stop offset="100%" stop-color="#1D4ED8" stop-opacity="0" />
    </radialGradient>
    <radialGradient id="amberGlow" cx="80%" cy="25%" r="45%">
      <stop offset="0%" stop-color="#F59E0B" stop-opacity="0.16" />
      <stop offset="100%" stop-color="#F59E0B" stop-opacity="0" />
    </radialGradient>

    <!-- Thermal Gradients -->
    <linearGradient id="banWarm" x1="0%" y1="100%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#EF4444" />
      <stop offset="50%" stop-color="#F97316" />
      <stop offset="100%" stop-color="#FBBF24" />
    </linearGradient>
    <linearGradient id="banCool" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#0284C7" />
      <stop offset="50%" stop-color="#0EA5E9" />
      <stop offset="100%" stop-color="#38BDF8" />
    </linearGradient>

    <!-- Unit Body Gradient -->
    <linearGradient id="unitGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#111F36" />
      <stop offset="100%" stop-color="#070E1A" />
    </linearGradient>

    <!-- Title Gradient -->
    <linearGradient id="brandTitleGrad" x1="0%" y1="0%" x2="100%" y2="0%">
      <stop offset="0%" stop-color="#60A5FA" />
      <stop offset="50%" stop-color="#38BDF8" />
      <stop offset="100%" stop-color="#93C5FD" />
    </linearGradient>

    <!-- Blade Gradient -->
    <linearGradient id="banBladeGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#64748B" />
      <stop offset="100%" stop-color="#1E293B" />
    </linearGradient>

    <!-- Drop Shadow & Glow -->
    <filter id="shadowBan" x="-10%" y="-10%" width="125%" height="125%">
      <feDropShadow dx="0" dy="16" stdDeviation="20" flood-color="#000000" flood-opacity="0.6"/>
    </filter>
    <filter id="glowBan" x="-20%" y="-20%" width="140%" height="140%">
      <feGaussianBlur stdDeviation="8" result="blur" />
      <feComposite in="SourceGraphic" in2="blur" operator="over" />
    </filter>
  </defs>

  <!-- Banner Background -->
  <rect width="1280" height="420" fill="url(#banBg)" />
  <rect width="1280" height="420" fill="url(#blueGlow)" />
  <rect width="1280" height="420" fill="url(#amberGlow)" />

  <!-- Technical Grid -->
  <g stroke="#1E2E48" stroke-width="1" opacity="0.22">
    <line x1="0" y1="70" x2="1280" y2="70" />
    <line x1="0" y1="140" x2="1280" y2="140" />
    <line x1="0" y1="210" x2="1280" y2="210" />
    <line x1="0" y1="280" x2="1280" y2="280" />
    <line x1="0" y1="350" x2="1280" y2="350" />
    <line x1="160" y1="0" x2="160" y2="420" />
    <line x1="320" y1="0" x2="320" y2="420" />
    <line x1="480" y1="0" x2="480" y2="420" />
    <line x1="640" y1="0" x2="640" y2="420" />
    <line x1="800" y1="0" x2="800" y2="420" />
    <line x1="960" y1="0" x2="960" y2="420" />
    <line x1="1120" y1="0" x2="1120" y2="420" />
  </g>

  <!-- Outer Frame -->
  <rect x="16" y="16" width="1248" height="388" rx="20" fill="none" stroke="#2563EB" stroke-width="2" stroke-opacity="0.3" />

  <!-- Left: High-Detail Heat Pump Unit (310 x 310 at x=85, y=55) -->
  <g transform="translate(85, 55)">
    <!-- Unit Cabinet (310 x 310) -->
    <rect x="15" y="15" width="280" height="280" rx="30" fill="url(#unitGrad)" stroke="#2563EB" stroke-width="2.5" stroke-opacity="0.5" filter="url(#shadowBan)"/>
    
    <!-- Thermal Energy Arcs around Fan -->
    <path d="M 155 87 A 88 88 0 0 1 243 175" fill="none" stroke="url(#banWarm)" stroke-width="9" stroke-linecap="round" opacity="0.95" filter="url(#glowBan)" />
    <path d="M 155 263 A 88 88 0 0 1 67 175" fill="none" stroke="url(#banCool)" stroke-width="9" stroke-linecap="round" opacity="0.95" filter="url(#glowBan)" />
    
    <!-- Top Header of Unit -->
    <text x="36" y="54" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="22" font-weight="900" fill="#FFFFFF" letter-spacing="3">SPRSUN</text>

    <!-- LCD Display -->
    <rect x="195" y="34" width="82" height="28" rx="6" fill="#040810" stroke="#1E2E44" stroke-width="1.5" />
    <circle cx="210" cy="48" r="4" fill="#10B981" filter="url(#glowBan)" />
    <text x="222" y="52" font-family="monospace" font-size="12" font-weight="bold" fill="#38BDF8">48°C</text>

    <!-- Divider Line -->
    <line x1="32" y1="74" x2="278" y2="74" stroke="#1E2E44" stroke-width="1.5" />

    <!-- Central Fan Housing -->
    <circle cx="155" cy="175" r="76" fill="#040810" stroke="#1E334D" stroke-width="3" />
    <circle cx="155" cy="175" r="62" fill="none" stroke="#162538" stroke-width="1.8" />
    <circle cx="155" cy="175" r="46" fill="none" stroke="#162538" stroke-width="1.5" />

    <!-- Radial Spokes -->
    <g stroke="#142232" stroke-width="1.8">
      <line x1="155" y1="100" x2="155" y2="250" />
      <line x1="80" y1="175" x2="230" y2="175" />
      <line x1="102" y1="122" x2="208" y2="228" />
      <line x1="102" y1="228" x2="208" y2="122" />
    </g>

    <!-- Fan Blades (4 blades) -->
    <g transform="rotate(25, 155, 175)">
      <path d="M 155 162 C 146 132 134 112 154 102 C 166 112 164 140 155 162 Z" fill="url(#banBladeGrad)" stroke="#475569" stroke-width="1"/>
      <path d="M 168 175 C 198 166 218 154 228 174 C 218 186 190 184 168 175 Z" fill="url(#banBladeGrad)" stroke="#475569" stroke-width="1"/>
      <path d="M 155 188 C 164 218 176 238 156 248 C 144 238 146 210 155 188 Z" fill="url(#banBladeGrad)" stroke="#475569" stroke-width="1"/>
      <path d="M 142 175 C 112 184 92 196 82 176 C 92 164 120 166 142 175 Z" fill="url(#banBladeGrad)" stroke="#475569" stroke-width="1"/>
    </g>

    <!-- Fan Hub -->
    <circle cx="155" cy="175" r="22" fill="#1E293B" stroke="#64748B" stroke-width="2" />
    <circle cx="151" cy="175" r="4" fill="#EF4444" />
    <circle cx="159" cy="175" r="4" fill="#0EA5E9" />

    <!-- Bottom Modbus Pill on Unit -->
    <rect x="75" y="260" width="160" height="24" rx="12" fill="#050C16" stroke="#1E334D" stroke-width="1.5"/>
    <circle cx="92" cy="272" r="3.5" fill="#10B981"/>
    <circle cx="106" cy="272" r="3" fill="#38BDF8"/>
    <circle cx="118" cy="272" r="3" fill="#F59E0B"/>
    <text x="130" y="276" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="10" font-weight="900" fill="#E2E8F0" letter-spacing="2.5">MODBUS</text>
  </g>

  <!-- Right: Title, Subtitle, Badges & Feature Cards -->
  <g transform="translate(470, 56)">
    <!-- Over-title Pill -->
    <g transform="translate(0, 0)">
      <rect x="0" y="0" width="220" height="30" rx="15" fill="#1E3A8A" fill-opacity="0.4" stroke="#3B82F6" stroke-width="1.5" />
      <circle cx="16" cy="15" r="4.5" fill="#38BDF8" />
      <text x="28" y="20" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="12" font-weight="700" fill="#93C5FD" letter-spacing="2">HOME ASSISTANT</text>
    </g>

    <!-- Main Title -->
    <text x="0" y="80" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="48" font-weight="900" fill="url(#brandTitleGrad)" letter-spacing="3">SPRSUN HEAT PUMP</text>
    <text x="0" y="122" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="28" font-weight="700" fill="#F8FAFC" letter-spacing="4">MODBUS INTEGRATION</text>

    <!-- Description -->
    <text x="0" y="158" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="16" font-weight="400" fill="#94A3B8">
      Full local monitoring and control for SPRSUN Heat Pumps via Modbus TCP &amp; RTU
    </text>

    <!-- Feature Highlights Grid (4 Pills) -->
    <g transform="translate(0, 190)">
      <!-- Pill 1: 100+ Entities -->
      <g transform="translate(0, 0)">
        <rect x="0" y="0" width="170" height="42" rx="10" fill="#101D30" stroke="#1E334D" stroke-width="1.5"/>
        <text x="16" y="26" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="13" font-weight="bold" fill="#38BDF8">📊 100+ Entities</text>
      </g>

      <!-- Pill 2: Fast Batch Read -->
      <g transform="translate(185, 0)">
        <rect x="0" y="0" width="170" height="42" rx="10" fill="#101D30" stroke="#1E334D" stroke-width="1.5"/>
        <text x="16" y="26" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="13" font-weight="bold" fill="#FBBF24">⚡ ~200ms Batch Read</text>
      </g>

      <!-- Pill 3: Local Polling -->
      <g transform="translate(370, 0)">
        <rect x="0" y="0" width="170" height="42" rx="10" fill="#101D30" stroke="#1E334D" stroke-width="1.5"/>
        <text x="16" y="26" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="13" font-weight="bold" fill="#34D399">🔒 100% Local (LAN)</text>
      </g>

      <!-- Pill 4: Carel & Chico -->
      <g transform="translate(555, 0)">
        <rect x="0" y="0" width="175" height="42" rx="10" fill="#101D30" stroke="#1E334D" stroke-width="1.5"/>
        <text x="16" y="26" font-family="DejaVu Sans, Fira Sans, sans-serif" font-size="13" font-weight="bold" fill="#A78BFA">🎛️ Carel &amp; Chico</text>
      </g>
    </g>

    <!-- Bottom Protocol Tags -->
    <g transform="translate(0, 255)">
      <rect x="0" y="0" width="134" height="28" rx="6" fill="#0EA5E9" fill-opacity="0.15" stroke="#0EA5E9" stroke-width="1.2" />
      <text x="12" y="19" font-family="monospace" font-size="12" font-weight="bold" fill="#38BDF8">Modbus TCP/RTU</text>

      <rect x="146" y="0" width="124" height="28" rx="6" fill="#10B981" fill-opacity="0.15" stroke="#10B981" stroke-width="1.2" />
      <text x="12" y="19" transform="translate(146, 0)" font-family="monospace" font-size="12" font-weight="bold" fill="#34D399">Elfin EW11/W11</text>

      <rect x="282" y="0" width="115" height="28" rx="6" fill="#F59E0B" fill-opacity="0.15" stroke="#F59E0B" stroke-width="1.2" />
      <text x="12" y="19" transform="translate(282, 0)" font-family="monospace" font-size="12" font-weight="bold" fill="#FBBF24">HACS Ready</text>
    </g>
  </g>
</svg>'''
    return svg

def main():
    import tempfile
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Save SVGs
        with open(os.path.join(tmp_dir, "icon.svg"), "w") as f:
            f.write(get_icon_svg(False))
        with open(os.path.join(tmp_dir, "dark_icon.svg"), "w") as f:
            f.write(get_icon_svg(True))
        with open(os.path.join(tmp_dir, "logo.svg"), "w") as f:
            f.write(get_logo_svg(False))
        with open(os.path.join(tmp_dir, "dark_logo.svg"), "w") as f:
            f.write(get_logo_svg(True))
        with open(os.path.join(tmp_dir, "banner.svg"), "w") as f:
            f.write(get_banner_svg())

        # Render Brand PNGs
        brand_renders = [
            ("icon.svg", os.path.join(BRAND_DIR, "icon.png"), 256, 256),
            ("icon.svg", os.path.join(BRAND_DIR, "icon@2x.png"), 512, 512),
            ("dark_icon.svg", os.path.join(BRAND_DIR, "dark_icon.png"), 256, 256),
            ("dark_icon.svg", os.path.join(BRAND_DIR, "dark_icon@2x.png"), 512, 512),
            ("logo.svg", os.path.join(BRAND_DIR, "logo.png"), 680, 200),
            ("logo.svg", os.path.join(BRAND_DIR, "logo@2x.png"), 1360, 400),
            ("dark_logo.svg", os.path.join(BRAND_DIR, "dark_logo.png"), 680, 200),
            ("dark_logo.svg", os.path.join(BRAND_DIR, "dark_logo@2x.png"), 1360, 400),
        ]
        images_renders = [
            ("banner.svg", os.path.join(IMAGES_DIR, "banner.png"), 1280, 420),
            ("icon.svg", os.path.join(IMAGES_DIR, "icon.png"), 512, 512),
            ("logo.svg", os.path.join(IMAGES_DIR, "logo.png"), 680, 200),
        ]

        for src, dst, w, h in brand_renders + images_renders:
            cmd = ["rsvg-convert", "-w", str(w), "-h", str(h), os.path.join(tmp_dir, src), "-o", dst]
            subprocess.run(cmd, check=True)
            im = Image.open(dst)
            print(f"Rendered {os.path.basename(dst)}: size={im.size}, mode={im.mode}")

if __name__ == "__main__":
    main()
