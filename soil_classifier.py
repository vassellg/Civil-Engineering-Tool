"""
USCS Soil Classification Tool
------------------------------
Classifies soils using the Unified Soil Classification System (USCS / ASTM D2487)
based on sieve analysis and Atterberg limit test inputs.

Outputs:
  - USCS symbol (e.g. CL, SW, GM)
  - Full classification name
  - Casagrande plasticity chart plot (for fine-grained soils)
  - Grain size distribution plot (for coarse-grained soils)

Author: [Your Name]
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np


# ── USCS Classification Logic ─────────────────────────────────────────────────

def classify_fine_grained(LL, PI):
    """
    Classify fine-grained soils (>50% passing #200 sieve).
    Uses Casagrande A-line: PI = 0.73 * (LL - 20)
    """
    A_line_PI = 0.73 * (LL - 20)

    if LL < 50:
        # Low plasticity
        if PI > A_line_PI and PI >= 7:
            symbol, name = "CL", "Lean Clay"
        elif PI < A_line_PI or PI < 4:
            symbol, name = "ML", "Silt of Low Plasticity"
        else:
            symbol, name = "CL-ML", "Silty Clay (Borderline)"
    else:
        # High plasticity
        if PI > A_line_PI:
            symbol, name = "CH", "Fat Clay"
        else:
            symbol, name = "MH", "Elastic Silt"

    # Special case: organic soils (would need LOI test — flagged for user)
    organic_flag = ""
    if LL < 50 and PI < A_line_PI:
        organic_flag = "  ⚠  If organic odor/dark color: consider OL (Organic Silt/Clay)"
    elif LL >= 50 and PI < A_line_PI:
        organic_flag = "  ⚠  If organic odor/dark color: consider OH (Organic Clay)"

    return symbol, name, organic_flag


def classify_coarse_grained(pct_gravel, pct_sand, pct_fines, Cu, Cc, fines_LL=None, fines_PI=None):
    """
    Classify coarse-grained soils (<50% passing #200 sieve).
    pct_gravel / pct_sand / pct_fines should sum to ~100.
    Cu = D60/D10, Cc = (D30^2) / (D10 * D60)
    """
    # Determine base: Gravel or Sand
    if pct_gravel > pct_sand:
        base = "G"
        well_graded = Cu >= 4 and 1 <= Cc <= 3
    else:
        base = "S"
        well_graded = Cu >= 6 and 1 <= Cc <= 3

    # Determine suffix based on fines content
    if pct_fines < 5:
        suffix = "W" if well_graded else "P"
        fines_type = ""
    elif pct_fines > 12:
        # Need Atterberg limits to classify fines
        if fines_LL is None or fines_PI is None:
            return None, "Atterberg limits required for soils with >12% fines", ""
        A_line_PI = 0.73 * (fines_LL - 20)
        if fines_PI >= 7 and fines_PI > A_line_PI:
            suffix, fines_type = "C", "Clayey"
        else:
            suffix, fines_type = "M", "Silty"
    else:
        # 5–12% fines: dual symbol
        w_p = "W" if well_graded else "P"
        if fines_LL is None or fines_PI is None:
            suffix = f"{w_p}-?M or {w_p}-?C"
            fines_type = "(Atterberg limits needed for dual symbol)"
        else:
            A_line_PI = 0.73 * (fines_LL - 20)
            f_suffix = "C" if (fines_PI >= 7 and fines_PI > A_line_PI) else "M"
            suffix = f"{w_p}-{base}{f_suffix}"
            fines_type = "Dual symbol"

    symbol = f"{base}{suffix}"

    name_map = {
        "GW": "Well-Graded Gravel", "GP": "Poorly-Graded Gravel",
        "GM": "Silty Gravel",       "GC": "Clayey Gravel",
        "SW": "Well-Graded Sand",   "SP": "Poorly-Graded Sand",
        "SM": "Silty Sand",         "SC": "Clayey Sand",
    }
    name = name_map.get(symbol, f"{fines_type} {'Gravel' if base == 'G' else 'Sand'} ({symbol})")

    return symbol, name, ""


# ── Plotting ──────────────────────────────────────────────────────────────────

def plot_casagrande(LL, PI, symbol):
    """Plot the Casagrande Plasticity Chart and mark the soil sample."""
    fig, ax = plt.subplots(figsize=(9, 6))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    LL_range = np.linspace(0, 110, 300)
    A_line  = np.maximum(0, 0.73 * (LL_range - 20))   # A-line
    U_line  = np.maximum(0, 0.90 * (LL_range - 8))    # U-line (upper bound)

    ax.plot(LL_range, A_line, color="#e94560", linewidth=2, label="A-line: PI = 0.73(LL−20)")
    ax.plot(LL_range, U_line, color="#f5a623", linewidth=1.5, linestyle="--", label="U-line: PI = 0.90(LL−8)")
    ax.axvline(x=50, color="#a8dadc", linewidth=1.2, linestyle=":", label="LL = 50")
    ax.axhline(y=7,  color="#a8dadc", linewidth=1.2, linestyle=":", label="PI = 7")

    # Zone labels
    zone_labels = [
        (20, 15, "CH\nFat Clay"),
        (70, 4,  "MH\nElastic Silt"),
        (25, 3,  "CL\nLean Clay"),
        (60, 15, "MH / OH"),
        (15, 1,  "ML/CL-ML"),
    ]
    for lx, py, txt in zone_labels:
        ax.text(lx, py, txt, color="#ccc", fontsize=8, alpha=0.7, ha="center")

    # Plot sample point
    ax.scatter([LL], [PI], color="#00ff88", s=120, zorder=5, label=f"Your sample: {symbol}")
    ax.annotate(f"  {symbol}", (LL, PI), color="#00ff88", fontsize=11, fontweight="bold")

    ax.set_xlim(0, 110)
    ax.set_ylim(0, 70)
    ax.set_xlabel("Liquid Limit (LL)", color="white", fontsize=11)
    ax.set_ylabel("Plasticity Index (PI)", color="white", fontsize=11)
    ax.set_title("Casagrande Plasticity Chart — USCS Classification", color="white", fontsize=13, pad=15)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")
    ax.legend(facecolor="#1a1a2e", edgecolor="#555", labelcolor="white", fontsize=9)

    plt.tight_layout()
    plt.savefig("casagrande_chart.png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print("  → Chart saved as 'casagrande_chart.png'")
    plt.show()


def plot_grain_size(Cu, Cc, symbol):
    """Approximate grain size distribution curve based on Cu and Cc."""
    fig, ax = plt.subplots(figsize=(9, 5))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    # Build an approximate S-curve using Cu and Cc
    D10 = 0.1
    D60 = D10 * Cu
    D30 = np.sqrt(Cc * D10 * D60)

    diameters = np.logspace(np.log10(D10 * 0.5), np.log10(D60 * 2), 200)
    passing = 10 + 80 / (1 + np.exp(-2.5 * (np.log10(diameters) - np.log10(D30))))

    ax.semilogx(diameters, passing, color="#00ff88", linewidth=2.5, label="Grain Size Curve")
    for d, label in [(D10, "D10"), (D30, "D30"), (D60, "D60")]:
        p = 10 + 80 / (1 + np.exp(-2.5 * (np.log10(d) - np.log10(D30))))
        ax.axvline(x=d, color="#f5a623", linewidth=1, linestyle="--", alpha=0.7)
        ax.scatter([d], [p], color="#f5a623", zorder=5)
        ax.text(d * 1.05, p + 2, label, color="#f5a623", fontsize=9)

    ax.set_xlabel("Grain Diameter (mm)", color="white", fontsize=11)
    ax.set_ylabel("% Passing", color="white", fontsize=11)
    ax.set_title(f"Approximate Grain Size Distribution — {symbol}  (Cu={Cu:.1f}, Cc={Cc:.2f})",
                 color="white", fontsize=12, pad=15)
    ax.set_ylim(0, 100)
    ax.tick_params(colors="white")
    for spine in ax.spines.values():
        spine.set_edgecolor("#444")
    ax.grid(True, which="both", color="#333", linestyle="--", alpha=0.5)
    ax.legend(facecolor="#1a1a2e", edgecolor="#555", labelcolor="white")

    plt.tight_layout()
    plt.savefig("grain_size_curve.png", dpi=150, bbox_inches="tight", facecolor=fig.get_facecolor())
    print("  → Chart saved as 'grain_size_curve.png'")
    plt.show()


# ── Main Program ──────────────────────────────────────────────────────────────

def get_float(prompt, allow_none=False):
    while True:
        val = input(prompt).strip()
        if allow_none and val == "":
            return None
        try:
            return float(val)
        except ValueError:
            print("  ✗ Please enter a valid number.")


def main():
    print("\n" + "="*55)
    print("   USCS SOIL CLASSIFICATION TOOL")
    print("   Based on ASTM D2487")
    print("="*55)

    pct_passing_200 = get_float("\nEnter % passing sieve #200: ")

    if pct_passing_200 > 50:
        # ── Fine-grained ──
        print("\n→ Fine-grained soil detected (>50% passing #200)\n")
        LL = get_float("  Liquid Limit (LL): ")
        PL = get_float("  Plastic Limit (PL): ")
        PI = LL - PL
        print(f"  Calculated PI = {PI:.1f}")

        symbol, name, flag = classify_fine_grained(LL, PI)

        print("\n" + "─"*55)
        print(f"  USCS Symbol : {symbol}")
        print(f"  Classification : {name}")
        if flag:
            print(flag)
        print("─"*55)

        plot_casagrande(LL, PI, symbol)

    else:
        # ── Coarse-grained ──
        print("\n→ Coarse-grained soil detected (<50% passing #200)\n")
        pct_fines  = pct_passing_200
        pct_gravel = get_float("  % retained on sieve #4 (gravel fraction): ")
        pct_sand   = max(0, 100 - pct_gravel - pct_fines)
        print(f"  Calculated sand fraction = {pct_sand:.1f}%")

        Cu = get_float("  Coefficient of Uniformity (Cu = D60/D10): ")
        Cc = get_float("  Coefficient of Curvature (Cc = D30²/(D10·D60)): ")

        fines_LL, fines_PI = None, None
        if pct_fines >= 5:
            print("\n  Fines ≥ 5% — Atterberg limits needed (press Enter to skip):")
            fines_LL = get_float("  Fines Liquid Limit (LL): ", allow_none=True)
            if fines_LL is not None:
                fines_PL = get_float("  Fines Plastic Limit (PL): ")
                fines_PI = fines_LL - fines_PL

        symbol, name, flag = classify_coarse_grained(
            pct_gravel, pct_sand, pct_fines, Cu, Cc, fines_LL, fines_PI
        )

        print("\n" + "─"*55)
        print(f"  USCS Symbol : {symbol}")
        print(f"  Classification : {name}")
        if flag:
            print(flag)
        print("─"*55)

        if symbol:
            plot_grain_size(Cu, Cc, symbol)

    print("\n✓ Classification complete.\n")


if __name__ == "__main__":
    main()
