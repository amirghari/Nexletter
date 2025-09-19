import sys, os
from typing import Dict, List, Tuple
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from db.connection import get_connection
from psycopg2.extras import RealDictCursor

# ====== USERS (labels → DB IDs) ======
USER_LABEL_TO_ID = {
    1: 12,  # U1
    2: 13,  # U2
    3: 14,  # U3
    4: 15,  # U4
    5: 16,  # U5
}

# ====== RANDOM BASELINE manual click positions (1-based in random top-10) ======
RANDOM_CLICK_POSITIONS: Dict[int, List[int]] = {
    1: [10, 2, 4],           # User 1
    2: [3, 7],               # User 2
    3: [4, 7, 10],           # User 3
    4: [1, 3, 4, 7, 10],     # User 4
    5: [2, 4, 5, 10, 6],     # User 5
}

ARTICLES_PER_USER = 10  # both systems show top-10

def fetch_ours_last10(conn, user_id: int):
    """
    Return the most recent <=10 OUR impressions for a user (scoring_config_id IS NOT NULL),
    ordered ASC by timestamp/id so that list index reflects rank (1..10).
    Each row -> {'id', 'clicked', 'timestamp'}
    """
    with conn.cursor(cursor_factory=RealDictCursor) as cur:
        cur.execute(
            """
            SELECT id, clicked, timestamp
            FROM recommendation_logs
            WHERE user_id = %s
              AND scoring_config_id IS NOT NULL
            ORDER BY timestamp ASC, id ASC
            LIMIT 10
            """,
            (user_id,),
        )
        return cur.fetchall()

def ctr(clicks: int, impressions: int) -> float:
    return (clicks / impressions) if impressions else 0.0

def precision_at_k(clicked_positions: List[int], k: int, list_len: int) -> float:
    """
    clicked_positions: list of 1-based positions clicked (subset of 1..list_len)
    k: cut-off
    """
    if list_len == 0:
        return 0.0
    k = min(k, list_len)
    hits = sum(1 for p in clicked_positions if 1 <= p <= k)
    return hits / k

def compute_random_metrics_per_user(label: int) -> Tuple[int, int, float, float]:
    """Return (impr, clicks, CTR, P@5) for random baseline for one user."""
    impr = ARTICLES_PER_USER
    clicks = len(RANDOM_CLICK_POSITIONS.get(label, []))
    p5 = precision_at_k(RANDOM_CLICK_POSITIONS.get(label, []), 5, ARTICLES_PER_USER)
    return impr, clicks, ctr(clicks, impr), p5

def compute_ours_metrics_per_user(conn, user_id: int) -> Tuple[int, int, float, float]:
    """
    Return (impr, clicks, CTR, P@5) for OUR recommender for one user,
    based on last <=10 OUR impressions. P@5 uses asc order as rank proxy.
    """
    rows = fetch_ours_last10(conn, user_id)
    impr = len(rows)
    clicks = sum(1 for r in rows if r.get("clicked"))
    c = ctr(clicks, impr)

    # derive clicked positions (1-based) from order ASC
    clicked_positions = []
    for idx, r in enumerate(rows, start=1):
        if r.get("clicked"):
            clicked_positions.append(idx)
    p5 = precision_at_k(clicked_positions, 5, impr)
    return impr, clicks, c, p5

def fmt_dec(x: float) -> str:
    return f"{x:.2f}"

def fmt_pct(x: float) -> str:
    return f"{100.0*x:.2f}%"

def ensure_reports_dir():
    out_dir = os.path.join(os.path.dirname(__file__), "..", "reports")
    os.makedirs(out_dir, exist_ok=True)
    return os.path.abspath(out_dir)

def save_csv(per_user_rows, totals_row, out_path):
    import csv
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["User", "System", "Impressions", "Clicks", "CTR", "Precision@5"])
        for row in per_user_rows:
            w.writerow(row)
        # totals
        w.writerow([])
        w.writerow(["TOTAL", "OURS", totals_row["ours_impr"], totals_row["ours_clicks"],
                    fmt_dec(totals_row["ours_ctr"]), fmt_dec(totals_row["ours_p5"])])
        w.writerow(["TOTAL", "RANDOM", totals_row["rnd_impr"], totals_row["rnd_clicks"],
                    fmt_dec(totals_row["rnd_ctr"]), fmt_dec(totals_row["rnd_p5"])])

def save_plots(per_user_metrics, out_dir):
    try:
        import matplotlib.pyplot as plt
        import numpy as np
    except Exception as e:
        print(f"⚠️ Skipping charts (matplotlib not available): {e}")
        return

    users = [m["user"] for m in per_user_metrics]
    ours_ctr_vals = [m["ours_ctr"] for m in per_user_metrics]
    rnd_ctr_vals  = [m["rnd_ctr"]  for m in per_user_metrics]
    ours_p5_vals  = [m["ours_p5"]  for m in per_user_metrics]
    rnd_p5_vals   = [m["rnd_p5"]   for m in per_user_metrics]

    x = np.arange(len(users))
    width = 0.35

    # CTR chart
    fig1, ax1 = plt.subplots()
    ax1.bar(x - width/2, ours_ctr_vals, width, label="Ours")
    ax1.bar(x + width/2, rnd_ctr_vals,  width, label="Random")
    ax1.set_ylabel("CTR")
    ax1.set_title("CTR by user (Ours vs Random)")
    ax1.set_xticks(x)
    ax1.set_xticklabels(users)
    ax1.legend()
    plt.tight_layout()
    ctr_path = os.path.join(out_dir, "ctr_comparison.png")
    plt.savefig(ctr_path, dpi=200)
    plt.close(fig1)

    # P@5 chart
    fig2, ax2 = plt.subplots()
    ax2.bar(x - width/2, ours_p5_vals, width, label="Ours")
    ax2.bar(x + width/2, rnd_p5_vals,  width, label="Random")
    ax2.set_ylabel("Precision@5")
    ax2.set_title("Precision@5 by user (Ours vs Random)")
    ax2.set_xticks(x)
    ax2.set_xticklabels(users)
    ax2.legend()
    plt.tight_layout()
    p5_path = os.path.join(out_dir, "p5_comparison.png")
    plt.savefig(p5_path, dpi=200)
    plt.close(fig2)

    print(f"🖼️ Charts saved:\n  • {ctr_path}\n  • {p5_path}")

def print_markdown_tables(per_user_metrics, totals):
    # Per-user (wide) table
    print("\n### Per-user metrics (Ours vs Random)\n")
    print("| User | Ours Impr | Ours Clicks | Ours CTR | Ours P@5 | Random Impr | Random Clicks | Random CTR | Random P@5 |")
    print("|------|-----------:|------------:|---------:|---------:|------------:|--------------:|-----------:|-----------:|")
    for m in per_user_metrics:
        print(f"| {m['user']} | {m['ours_impr']} | {m['ours_clicks']} | {fmt_pct(m['ours_ctr'])} | {fmt_pct(m['ours_p5'])} | "
              f"{m['rnd_impr']} | {m['rnd_clicks']} | {fmt_pct(m['rnd_ctr'])} | {fmt_pct(m['rnd_p5'])} |")

    # Totals
    print("\n### Totals")
    print("| System | Impressions | Clicks | CTR | Precision@5 |")
    print("|--------|------------:|-------:|----:|------------:|")
    print(f"| Ours   | {totals['ours_impr']} | {totals['ours_clicks']} | {fmt_pct(totals['ours_ctr'])} | {fmt_pct(totals['ours_p5'])} |")
    print(f"| Random | {totals['rnd_impr']} | {totals['rnd_clicks']} | {fmt_pct(totals['rnd_ctr'])} | {fmt_pct(totals['rnd_p5'])} |")

def save_markdown_tables(per_user_metrics, totals, out_dir):
    md_path = os.path.join(out_dir, "metrics_table.md")
    with open(md_path, "w", encoding="utf-8") as f:
        f.write("### Per-user metrics (Ours vs Random)\n\n")
        f.write("| User | Ours Impr | Ours Clicks | Ours CTR | Ours P@5 | Random Impr | Random Clicks | Random CTR | Random P@5 |\n")
        f.write("|------|-----------:|------------:|---------:|---------:|------------:|--------------:|-----------:|-----------:|\n")
        for m in per_user_metrics:
            f.write(f"| {m['user']} | {m['ours_impr']} | {m['ours_clicks']} | {fmt_pct(m['ours_ctr'])} | {fmt_pct(m['ours_p5'])} | "
                    f"{m['rnd_impr']} | {m['rnd_clicks']} | {fmt_pct(m['rnd_ctr'])} | {fmt_pct(m['rnd_p5'])} |\n")
        f.write("\n### Totals\n\n")
        f.write("| System | Impressions | Clicks | CTR | Precision@5 |\n")
        f.write("|--------|------------:|-------:|----:|------------:|\n")
        f.write(f"| Ours   | {totals['ours_impr']} | {totals['ours_clicks']} | {fmt_pct(totals['ours_ctr'])} | {fmt_pct(totals['ours_p5'])} |\n")
        f.write(f"| Random | {totals['rnd_impr']} | {totals['rnd_clicks']} | {fmt_pct(totals['rnd_ctr'])} | {fmt_pct(totals['rnd_p5'])} |\n")
    print(f"📝 Markdown table saved: {md_path}")

def save_latex_tables(per_user_metrics, totals, out_dir):
    tex_path = os.path.join(out_dir, "metrics_table.tex")
    with open(tex_path, "w", encoding="utf-8") as f:
        f.write("% Auto-generated metrics table (Ours vs Random)\n")
        f.write("\\begin{table}[t]\n\\centering\n\\small\n")
        f.write("\\caption{Per-user comparison of CTR and Precision@5 between our recommender and a random baseline.}\n")
        f.write("\\label{tab:recsys_per_user}\n")
        f.write("\\begin{tabular}{lrrrrrrrr}\n\\toprule\n")
        f.write("User & Ours Impr & Ours Clicks & Ours CTR & Ours P@5 & Rand Impr & Rand Clicks & Rand CTR & Rand P@5 \\\\\n")
        f.write("\\midrule\n")
        for m in per_user_metrics:
            f.write(f"{m['user']} & {m['ours_impr']} & {m['ours_clicks']} & {fmt_pct(m['ours_ctr'])} & {fmt_pct(m['ours_p5'])} & "
                    f"{m['rnd_impr']} & {m['rnd_clicks']} & {fmt_pct(m['rnd_ctr'])} & {fmt_pct(m['rnd_p5'])} \\\\\n")
        f.write("\\midrule\n")
        f.write(f"\\textbf{{Totals}} & {totals['ours_impr']} & {totals['ours_clicks']} & {fmt_pct(totals['ours_ctr'])} & {fmt_pct(totals['ours_p5'])} & "
                f"{totals['rnd_impr']} & {totals['rnd_clicks']} & {fmt_pct(totals['rnd_ctr'])} & {fmt_pct(totals['rnd_p5'])} \\\\\n")
        f.write("\\bottomrule\n\\end{tabular}\n\\end{table}\n")
    print(f"📄 LaTeX table saved: {tex_path}")

def main():
    conn = get_connection()

    per_user_metrics = []
    ours_impr_total = ours_clicks_total = 0
    rnd_impr_total  = rnd_clicks_total  = 0
    ours_p5_acc = rnd_p5_acc = 0.0
    users_count = 0

    for label in sorted(USER_LABEL_TO_ID.keys()):
        user_id = USER_LABEL_TO_ID[label]
        user_tag = f"U{label}"

        # OURS
        o_impr, o_clicks, o_ctr, o_p5 = compute_ours_metrics_per_user(conn, user_id)
        # RANDOM
        r_impr, r_clicks, r_ctr, r_p5 = compute_random_metrics_per_user(label)

        per_user_metrics.append({
            "user": user_tag,
            "ours_impr": o_impr, "ours_clicks": o_clicks, "ours_ctr": o_ctr, "ours_p5": o_p5,
            "rnd_impr": r_impr,  "rnd_clicks": r_clicks,  "rnd_ctr": r_ctr,  "rnd_p5": r_p5,
        })

        ours_impr_total += o_impr
        ours_clicks_total += o_clicks
        rnd_impr_total  += r_impr
        rnd_clicks_total += r_clicks
        ours_p5_acc += o_p5
        rnd_p5_acc  += r_p5
        users_count += 1

    conn.close()

    totals = {
        "ours_impr": ours_impr_total,
        "ours_clicks": ours_clicks_total,
        "ours_ctr": ctr(ours_clicks_total, ours_impr_total),
        "ours_p5": (ours_p5_acc / users_count) if users_count else 0.0,  # macro-avg P@5
        "rnd_impr": rnd_impr_total,
        "rnd_clicks": rnd_clicks_total,
        "rnd_ctr": ctr(rnd_clicks_total, rnd_impr_total),
        "rnd_p5": (rnd_p5_acc / users_count) if users_count else 0.0,     # macro-avg P@5
    }

    # Console summary (Markdown)
    print_markdown_tables(per_user_metrics, totals)

    # Save CSV + charts + tables
    out_dir = ensure_reports_dir()
    # CSV rows (per-user, both systems stacked)
    per_user_rows = (
        [[m["user"], "System",  m["ours_impr"], m["ours_clicks"], fmt_dec(m["ours_ctr"]), fmt_dec(m["ours_p5"])]
         for m in per_user_metrics] +
        [[m["user"], "RANDOM", m["rnd_impr"], m["rnd_clicks"], fmt_dec(m["rnd_ctr"]), fmt_dec(m["rnd_p5"])]
         for m in per_user_metrics]
    )
    save_csv(per_user_rows, totals, os.path.join(out_dir, "metrics.csv"))
    save_plots(per_user_metrics, out_dir)
    save_markdown_tables(per_user_metrics, totals, out_dir)
    save_latex_tables(per_user_metrics, totals, out_dir)

    print("\n✅ Report complete.")

if __name__ == "__main__":
    main()