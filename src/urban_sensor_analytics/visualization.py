"""生成无需外部依赖的中文可视化仪表板。"""

from __future__ import annotations

from html import escape
from pathlib import Path


COLORS = ("#2563eb", "#0f766e", "#d97706", "#7c3aed", "#dc2626")


def _bar_chart(
    rows: list[tuple[str, float]], title: str, unit: str, width: int = 720
) -> str:
    """以 SVG 横向条形图展示一组带标签的数值。"""
    height = max(180, 72 + 44 * len(rows))
    maximum = max((value for _, value in rows), default=1) or 1
    chart_width = width - 250
    elements = [
        f'<svg viewBox="0 0 {width} {height}" role="img" aria-label="{escape(title)}">',
        f'<text x="20" y="32" class="chart-title">{escape(title)}</text>',
    ]
    if not rows:
        elements.append('<text x="20" y="82" class="empty">暂无符合阈值的数据</text>')
    for index, (label, value) in enumerate(rows):
        y = 58 + index * 44
        bar_width = max(2, value / maximum * chart_width)
        color = COLORS[index % len(COLORS)]
        elements.extend(
            [
                f'<text x="20" y="{y + 18}" class="axis-label">{escape(label)}</text>',
                f'<rect x="185" y="{y}" width="{bar_width:.1f}" height="24" rx="6" fill="{color}"/>',
                f'<text x="{195 + bar_width:.1f}" y="{y + 18}" class="value">{value:.2f}{escape(unit)}</text>',
            ]
        )
    elements.append("</svg>")
    return "".join(elements)


def _dashboard_body(report: dict[str, object]) -> tuple[str, str]:
    latency = list(report.get("延迟异常", []))
    risks = list(report.get("空气质量风险", []))
    matches = list(report.get("空间文本匹配", []))

    latency_rows = [
        (f'{row["设备编号"]} · {row["日期"]}', float(row["延迟增幅（毫秒）"]))
        for row in latency
    ]
    risk_rows = [
        (str(row["设备编号"]), float(row["高风险日期数"])) for row in risks
    ]
    latency_chart = _bar_chart(latency_rows, "设备延迟异常增幅", " 毫秒")
    risk_chart = _bar_chart(risk_rows, "各设备高风险日期数量", " 天")

    table_rows = "".join(
        "<tr>"
        f'<td>{escape(str(row["监测点编号"]))}</td>'
        f'<td>{escape(str(row["事件编号"]))}</td>'
        f'<td>{float(row["空间距离"]):.2f}</td>'
        f'<td><span class="score"><i style="width:{float(row["杰卡德相似度"]) * 100:.0f}%"></i></span>'
        f'{float(row["杰卡德相似度"]):.2f}</td>'
        "</tr>"
        for row in matches
    ) or '<tr><td colspan="4" class="empty-cell">暂无符合双重阈值的匹配结果</td></tr>'

    cards = f"""
    <section class="cards">
      <article><strong>{len(latency)}</strong><span>延迟异常记录</span></article>
      <article><strong>{len(risks)}</strong><span>高风险设备</span></article>
      <article><strong>{sum(int(row['高风险日期数']) for row in risks)}</strong><span>高风险设备日期</span></article>
      <article><strong>{len(matches)}</strong><span>空间文本关联</span></article>
    </section>"""
    content = f"""
    {cards}
    <section class="grid">
      <article class="panel">{latency_chart}</article>
      <article class="panel">{risk_chart}</article>
    </section>
    <section class="panel matches">
      <h2>异常监测点与周边事件关联</h2>
      <table>
        <thead><tr><th>监测点</th><th>事件</th><th>空间距离</th><th>文本相似度</th></tr></thead>
        <tbody>{table_rows}</tbody>
      </table>
    </section>"""
    preview = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="650" viewBox="0 0 1200 650">
      <style>text{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif;fill:#172033}}.t{{font-size:30px;font-weight:700}}.s{{font-size:15px;fill:#64748b}}.n{{font-size:34px;font-weight:700;fill:#0f766e}}.l{{font-size:14px}}.v{{font-size:13px;fill:#475569}}</style>
      <rect width="1200" height="650" rx="28" fill="#f5f7fb"/><text x="55" y="62" class="t">城市环境传感器风险监测仪表板</text><text x="55" y="91" class="s">MapReduce · Spark RDD/DataFrame · 空间文本联合分析</text>
      <g transform="translate(55 125)"><rect width="250" height="110" rx="18" fill="white"/><text x="24" y="50" class="n">{len(latency)}</text><text x="24" y="82" class="s">延迟异常记录</text></g>
      <g transform="translate(335 125)"><rect width="250" height="110" rx="18" fill="white"/><text x="24" y="50" class="n">{len(risks)}</text><text x="24" y="82" class="s">高风险设备</text></g>
      <g transform="translate(615 125)"><rect width="250" height="110" rx="18" fill="white"/><text x="24" y="50" class="n">{sum(int(row['高风险日期数']) for row in risks)}</text><text x="24" y="82" class="s">高风险设备日期</text></g>
      <g transform="translate(895 125)"><rect width="250" height="110" rx="18" fill="white"/><text x="24" y="50" class="n">{len(matches)}</text><text x="24" y="82" class="s">空间文本关联</text></g>
      <rect x="55" y="270" width="1090" height="320" rx="20" fill="white"/><text x="85" y="315" font-size="21" font-weight="700">延迟异常增幅与空气质量风险概览</text>
      {_preview_bars(latency_rows, 85, 350, 480, '#2563eb', '毫秒')}
      {_preview_bars(risk_rows, 635, 350, 430, '#0f766e', '天')}
    </svg>"""
    return content, preview


def _preview_bars(
    rows: list[tuple[str, float]], x: int, y: int, width: int, color: str, unit: str
) -> str:
    maximum = max((value for _, value in rows), default=1) or 1
    parts = []
    for index, (label, value) in enumerate(rows[:5]):
        row_y = y + index * 44
        bar_width = max(3, value / maximum * (width - 170))
        parts.append(
            f'<text x="{x}" y="{row_y + 17}" class="l">{escape(label[:18])}</text>'
            f'<rect x="{x + 145}" y="{row_y}" width="{bar_width:.1f}" height="23" rx="5" fill="{color}" opacity=".88"/>'
            f'<text x="{x + 155 + bar_width:.1f}" y="{row_y + 17}" class="v">{value:.1f}{unit}</text>'
        )
    return "".join(parts)


def write_dashboard(
    report: dict[str, object], output_path: Path, preview_path: Path | None = None
) -> None:
    """写入自包含 HTML 仪表板，并可选生成供 README 展示的 SVG 预览图。"""
    content, preview = _dashboard_body(report)
    html = f"""<!doctype html>
<html lang="zh-CN"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>城市环境传感器风险监测仪表板</title>
<style>
:root{{--ink:#172033;--muted:#64748b;--line:#e2e8f0;--bg:#f5f7fb;--panel:#fff;--blue:#2563eb;--teal:#0f766e}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font-family:-apple-system,BlinkMacSystemFont,"Segoe UI","Microsoft YaHei",sans-serif}}
main{{max-width:1280px;margin:auto;padding:44px 28px 70px}}header{{margin-bottom:28px}}h1{{font-size:34px;margin:0 0 8px}}header p{{margin:0;color:var(--muted)}}
.cards{{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:18px}}.cards article,.panel{{background:var(--panel);border:1px solid var(--line);border-radius:18px;box-shadow:0 10px 32px rgba(15,23,42,.05)}}.cards article{{padding:22px}}.cards strong{{display:block;font-size:34px;color:var(--teal)}}.cards span{{color:var(--muted)}}
.grid{{display:grid;grid-template-columns:1fr 1fr;gap:18px}}.panel{{padding:16px;overflow:auto}}svg{{width:100%;height:auto}}.chart-title{{font-size:20px;font-weight:700;fill:var(--ink)}}.axis-label,.value{{font-size:13px;fill:#475569}}.empty{{font-size:15px;fill:var(--muted)}}
.matches{{margin-top:18px;padding:24px}}h2{{font-size:21px;margin:0 0 18px}}table{{width:100%;border-collapse:collapse}}th,td{{padding:13px 12px;border-bottom:1px solid var(--line);text-align:left}}th{{color:var(--muted);font-size:13px}}.score{{display:inline-block;width:110px;height:8px;background:#e2e8f0;border-radius:8px;margin-right:10px;vertical-align:middle}}.score i{{display:block;height:100%;background:var(--blue);border-radius:8px}}.empty-cell{{text-align:center;color:var(--muted)}}
@media(max-width:850px){{.cards{{grid-template-columns:1fr 1fr}}.grid{{grid-template-columns:1fr}}}}@media(max-width:520px){{main{{padding:24px 14px}}h1{{font-size:27px}}.cards{{grid-template-columns:1fr}}}}
</style></head><body><main><header><h1>城市环境传感器风险监测仪表板</h1><p>MapReduce、Spark RDD/DataFrame 与空间文本联合分析的综合结果</p></header>{content}</main></body></html>"""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    if preview_path is not None:
        preview_path.parent.mkdir(parents=True, exist_ok=True)
        preview_path.write_text(preview, encoding="utf-8")
