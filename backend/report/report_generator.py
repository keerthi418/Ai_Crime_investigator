from pathlib import Path
from datetime import datetime
import textwrap

import matplotlib
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import networkx as nx

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
    Image,
    KeepTogether,
)
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics


BASE_DIR = Path(__file__).resolve().parents[2]
REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


# ============================================================
# COLORS
# ============================================================

NAVY = colors.HexColor("#0F172A")
BLUE = colors.HexColor("#1D4ED8")
LIGHT_BLUE = colors.HexColor("#EFF6FF")
CYAN = colors.HexColor("#0891B2")

GREEN = colors.HexColor("#16A34A")
LIGHT_GREEN = colors.HexColor("#DCFCE7")

RED = colors.HexColor("#DC2626")
LIGHT_RED = colors.HexColor("#FEE2E2")

ORANGE = colors.HexColor("#EA580C")
LIGHT_ORANGE = colors.HexColor("#FFEDD5")

PURPLE = colors.HexColor("#7C3AED")
LIGHT_PURPLE = colors.HexColor("#EDE9FE")

GRAY_900 = colors.HexColor("#111827")
GRAY_700 = colors.HexColor("#374151")
GRAY_600 = colors.HexColor("#4B5563")
GRAY_500 = colors.HexColor("#6B7280")
GRAY_400 = colors.HexColor("#9CA3AF")
GRAY_300 = colors.HexColor("#D1D5DB")
GRAY_200 = colors.HexColor("#E5E7EB")
GRAY_100 = colors.HexColor("#F3F4F6")
GRAY_50 = colors.HexColor("#F9FAFB")
WHITE = colors.white


# ============================================================
# FONT
# ============================================================

def register_fonts():
    """
    Try to use Arial if available.
    Fall back to Helvetica when Arial is not available.
    """

    windows_fonts = Path("C:/Windows/Fonts")

    regular = windows_fonts / "arial.ttf"
    bold = windows_fonts / "arialbd.ttf"
    italic = windows_fonts / "ariali.ttf"

    if regular.exists() and bold.exists():

        try:
            pdfmetrics.registerFont(
                TTFont("ArialCustom", str(regular))
            )

            pdfmetrics.registerFont(
                TTFont("ArialCustom-Bold", str(bold))
            )

            if italic.exists():
                pdfmetrics.registerFont(
                    TTFont("ArialCustom-Italic", str(italic))
                )

            return "ArialCustom", "ArialCustom-Bold"

        except Exception:
            pass

    return "Helvetica", "Helvetica-Bold"


FONT_REGULAR, FONT_BOLD = register_fonts()


# ============================================================
# PDF HEADER / FOOTER
# ============================================================

def draw_header_footer(canvas, doc):

    canvas.saveState()

    width, height = A4

    # Header line
    canvas.setStrokeColor(BLUE)
    canvas.setLineWidth(1.2)

    canvas.line(
        18 * mm,
        height - 16 * mm,
        width - 18 * mm,
        height - 16 * mm
    )

    # Header title
    canvas.setFont(FONT_BOLD, 8)

    canvas.setFillColor(NAVY)

    canvas.drawString(
        18 * mm,
        height - 12 * mm,
        "AI CRIME INVESTIGATOR"
    )

    canvas.setFont(FONT_REGULAR, 7)

    canvas.setFillColor(GRAY_500)

    canvas.drawRightString(
        width - 18 * mm,
        height - 12 * mm,
        "AI-Assisted Investigation Report"
    )

    # Footer line
    canvas.setStrokeColor(GRAY_300)
    canvas.setLineWidth(0.5)

    canvas.line(
        18 * mm,
        15 * mm,
        width - 18 * mm,
        15 * mm
    )

    # Footer
    canvas.setFont(FONT_REGULAR, 7)

    canvas.setFillColor(GRAY_500)

    canvas.drawString(
        18 * mm,
        9 * mm,
        "Confidential Investigation Report"
    )

    canvas.drawRightString(
        width - 18 * mm,
        9 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# ============================================================
# SAFE TEXT
# ============================================================

def safe_text(value):

    if value is None:
        return ""

    return str(value)


# ============================================================
# WRAP LONG TEXT
# ============================================================

def wrap_text(text, width=110):

    text = safe_text(text)

    if not text:
        return ""

    return "\n".join(
        textwrap.wrap(
            text,
            width=width,
            break_long_words=False
        )
    )


# ============================================================
# GRAPH GENERATOR
# ============================================================

def generate_graph_image(
    graph_data,
    relations=None,
    entities=None,
    start=None,
    target=None
):

    relations = relations or []
    entities = entities or []

    graph = nx.DiGraph()

    # --------------------------------------------------------
    # Add entities
    # --------------------------------------------------------

    for entity in entities:

        if isinstance(entity, dict):

            name = (
                entity.get("text")
                or entity.get("name")
                or entity.get("id")
            )

            entity_type = (
                entity.get("type")
                or "PERSON"
            )

        else:

            name = str(entity)
            entity_type = "PERSON"

        if name:
            graph.add_node(
                str(name),
                entity_type=str(entity_type).upper()
            )

    # --------------------------------------------------------
    # Add graph nodes
    # --------------------------------------------------------

    if isinstance(graph_data, dict):

        nodes = graph_data.get("nodes", [])

        for node in nodes:

            if isinstance(node, dict):

                node_id = (
                    node.get("id")
                    or node.get("name")
                    or node.get("label")
                )

                node_type = (
                    node.get("type")
                    or node.get("entity_type")
                    or "PERSON"
                )

            else:

                node_id = str(node)
                node_type = "PERSON"

            if node_id:

                graph.add_node(
                    str(node_id),
                    entity_type=str(node_type).upper()
                )

    # --------------------------------------------------------
    # Add relations
    # --------------------------------------------------------

    for relation in relations:

        if not isinstance(relation, dict):
            continue

        source = relation.get("source")
        target_node = relation.get("target")

        if not source or not target_node:
            continue

        relation_name = (
            relation.get("relation")
            or relation.get("type")
            or "related_to"
        )

        graph.add_node(
            str(source),
            entity_type="PERSON"
        )

        graph.add_node(
            str(target_node),
            entity_type="PERSON"
        )

        graph.add_edge(
            str(source),
            str(target_node),
            relation=str(relation_name)
        )

    # --------------------------------------------------------
    # If graph_data contains edges
    # --------------------------------------------------------

    if isinstance(graph_data, dict):

        edges = graph_data.get("edges", [])

        for edge in edges:

            if isinstance(edge, dict):

                source = (
                    edge.get("source")
                    or edge.get("from")
                )

                target_node = (
                    edge.get("target")
                    or edge.get("to")
                )

                relation_name = (
                    edge.get("relation")
                    or edge.get("label")
                    or edge.get("type")
                    or "related_to"
                )

            else:
                continue

            if source and target_node:

                graph.add_edge(
                    str(source),
                    str(target_node),
                    relation=str(relation_name)
                )

    # --------------------------------------------------------
    # Empty graph protection
    # --------------------------------------------------------

    if len(graph.nodes) == 0:

        return None

    # --------------------------------------------------------
    # Figure
    # --------------------------------------------------------

    fig = plt.figure(
        figsize=(12, 7),
        dpi=180
    )

    ax = fig.add_subplot(111)

    ax.set_facecolor("#F8FAFC")

    # --------------------------------------------------------
    # Layout
    # --------------------------------------------------------

    try:

        if len(graph.nodes) <= 3:

            pos = nx.spring_layout(
                graph,
                seed=42,
                k=2.5
            )

        elif len(graph.nodes) <= 10:

            pos = nx.spring_layout(
                graph,
                seed=42,
                k=3.0,
                iterations=120
            )

        else:

            pos = nx.kamada_kawai_layout(
                graph
            )

    except Exception:

        pos = nx.spring_layout(
            graph,
            seed=42
        )

    # --------------------------------------------------------
    # Node groups
    # --------------------------------------------------------

    person_nodes = []
    evidence_nodes = []
    location_nodes = []
    date_nodes = []
    other_nodes = []

    for node, data in graph.nodes(data=True):

        node_type = str(
            data.get("entity_type", "PERSON")
        ).upper()

        if "EVIDENCE" in node_type:

            evidence_nodes.append(node)

        elif "LOCATION" in node_type:

            location_nodes.append(node)

        elif "DATE" in node_type:

            date_nodes.append(node)

        elif "PERSON" in node_type:

            person_nodes.append(node)

        else:

            other_nodes.append(node)

    # --------------------------------------------------------
    # Person nodes
    # --------------------------------------------------------

    if person_nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=person_nodes,
            node_color="#DBEAFE",
            edgecolors="#1D4ED8",
            node_size=1800,
            node_shape="o",
            linewidths=2,
            ax=ax
        )

    # --------------------------------------------------------
    # Evidence nodes
    # --------------------------------------------------------

    if evidence_nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=evidence_nodes,
            node_color="#FEF3C7",
            edgecolors="#D97706",
            node_size=1900,
            node_shape="s",
            linewidths=2,
            ax=ax
        )

    # --------------------------------------------------------
    # Location nodes
    # --------------------------------------------------------

    if location_nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=location_nodes,
            node_color="#DCFCE7",
            edgecolors="#16A34A",
            node_size=1900,
            node_shape="D",
            linewidths=2,
            ax=ax
        )

    # --------------------------------------------------------
    # Date nodes
    # --------------------------------------------------------

    if date_nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=date_nodes,
            node_color="#CFFAFE",
            edgecolors="#0891B2",
            node_size=1800,
            node_shape="^",
            linewidths=2,
            ax=ax
        )

    # --------------------------------------------------------
    # Other nodes
    # --------------------------------------------------------

    if other_nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=other_nodes,
            node_color="#EDE9FE",
            edgecolors="#7C3AED",
            node_size=1800,
            node_shape="o",
            linewidths=2,
            ax=ax
        )

    # --------------------------------------------------------
    # Start node
    # --------------------------------------------------------

    if start and start in graph.nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=[start],
            node_color="#BBF7D0",
            edgecolors="#15803D",
            node_size=2200,
            node_shape="o",
            linewidths=3,
            ax=ax
        )

    # --------------------------------------------------------
    # Target node
    # --------------------------------------------------------

    if target and target in graph.nodes:

        nx.draw_networkx_nodes(
            graph,
            pos,
            nodelist=[target],
            node_color="#FECACA",
            edgecolors="#B91C1C",
            node_size=2200,
            node_shape="o",
            linewidths=3,
            ax=ax
        )

    # --------------------------------------------------------
    # Edges
    # --------------------------------------------------------

    nx.draw_networkx_edges(
        graph,
        pos,
        edge_color="#64748B",
        width=1.8,
        arrows=True,
        arrowsize=18,
        connectionstyle="arc3,rad=0.08",
        node_size=1800,
        ax=ax
    )

    # --------------------------------------------------------
    # Labels
    # --------------------------------------------------------

    labels = {}

    for node in graph.nodes:

        node_text = str(node)

        if len(node_text) > 22:

            node_text = (
                node_text[:19] + "..."
            )

        labels[node] = node_text

    nx.draw_networkx_labels(
        graph,
        pos,
        labels=labels,
        font_size=8,
        font_weight="bold",
        font_color="#0F172A",
        ax=ax
    )

    # --------------------------------------------------------
    # Edge labels
    # --------------------------------------------------------

    edge_labels = {}

    for source, target_node, data in graph.edges(
        data=True
    ):

        relation_name = data.get(
            "relation",
            "related_to"
        )

        edge_labels[
            (source, target_node)
        ] = relation_name

    if edge_labels:

        nx.draw_networkx_edge_labels(
            graph,
            pos,
            edge_labels=edge_labels,
            font_size=7,
            font_color="#475569",
            bbox=dict(
                alpha=0.85,
                color="white",
                pad=0.25
            ),
            ax=ax
        )

    # --------------------------------------------------------
    # Title
    # --------------------------------------------------------

    ax.set_title(
        "Investigation Knowledge Graph",
        fontsize=15,
        fontweight="bold",
        color="#0F172A",
        pad=18
    )

    # --------------------------------------------------------
    # Legend
    # --------------------------------------------------------

    from matplotlib.lines import Line2D

    legend_items = [
        Line2D(
            [0],
            [0],
            marker="o",
            color="w",
            label="Person",
            markerfacecolor="#DBEAFE",
            markeredgecolor="#1D4ED8",
            markersize=10
        ),
        Line2D(
            [0],
            [0],
            marker="s",
            color="w",
            label="Evidence",
            markerfacecolor="#FEF3C7",
            markeredgecolor="#D97706",
            markersize=10
        ),
        Line2D(
            [0],
            [0],
            marker="D",
            color="w",
            label="Location",
            markerfacecolor="#DCFCE7",
            markeredgecolor="#16A34A",
            markersize=10
        ),
        Line2D(
            [0],
            [0],
            marker="^",
            color="w",
            label="Date",
            markerfacecolor="#CFFAFE",
            markeredgecolor="#0891B2",
            markersize=10
        ),
    ]

    if start:

        legend_items.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="Start",
                markerfacecolor="#BBF7D0",
                markeredgecolor="#15803D",
                markersize=10
            )
        )

    if target:

        legend_items.append(
            Line2D(
                [0],
                [0],
                marker="o",
                color="w",
                label="Target",
                markerfacecolor="#FECACA",
                markeredgecolor="#B91C1C",
                markersize=10
            )
        )

    ax.legend(
        handles=legend_items,
        loc="upper center",
        bbox_to_anchor=(0.5, -0.02),
        ncol=4,
        frameon=False,
        fontsize=8
    )

    ax.axis("off")

    plt.tight_layout()

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S_%f"
    )

    image_path = (
        REPORTS_DIR
        / f"investigation_graph_{timestamp}.png"
    )

    fig.savefig(
        image_path,
        bbox_inches="tight",
        facecolor="white"
    )

    plt.close(fig)

    return image_path


# ============================================================
# CREATE PDF
# ============================================================

def generate_pdf_report(
    entities=None,
    relations=None,
    graph_data=None,
    start=None,
    target=None,
    bfs_path=None,
    dfs_path=None,
    astar_path=None,
    confidence=None,
    contradictions=None,
    explanation=None,
    username=None,
    case_text=None,
    **kwargs
):

    entities = entities or []
    relations = relations or []
    bfs_path = bfs_path or []
    dfs_path = dfs_path or []
    astar_path = astar_path or []
    contradictions = contradictions or []

    # --------------------------------------------------------
    # File name
    # --------------------------------------------------------

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    pdf_path = (
        REPORTS_DIR
        / f"crime_investigation_{timestamp}.pdf"
    )

    # --------------------------------------------------------
    # Document
    # --------------------------------------------------------

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,

        # PROFESSIONAL MARGINS
        rightMargin=18 * mm,
        leftMargin=18 * mm,
        topMargin=24 * mm,
        bottomMargin=22 * mm,

        title="AI Crime Investigator Report",
        author="AI Crime Investigator",
        subject="AI-assisted crime investigation report"
    )

    styles = getSampleStyleSheet()

    # --------------------------------------------------------
    # Custom styles
    # --------------------------------------------------------

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Title"],
        fontName=FONT_BOLD,
        fontSize=23,
        leading=28,
        textColor=NAVY,
        alignment=TA_LEFT,
        spaceAfter=8
    )

    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=10,
        leading=15,
        textColor=GRAY_600,
        spaceAfter=18
    )

    section_style = ParagraphStyle(
        "Section",
        parent=styles["Heading2"],
        fontName=FONT_BOLD,
        fontSize=14,
        leading=18,
        textColor=NAVY,
        spaceBefore=14,
        spaceAfter=9
    )

    body_style = ParagraphStyle(
        "Body",
        parent=styles["BodyText"],
        fontName=FONT_REGULAR,
        fontSize=9.5,
        leading=15,
        textColor=GRAY_700,
        spaceAfter=7
    )

    small_style = ParagraphStyle(
        "Small",
        parent=styles["BodyText"],
        fontName=FONT_REGULAR,
        fontSize=8,
        leading=12,
        textColor=GRAY_600
    )

    table_header_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=8,
        textColor=WHITE,
        leading=10
    )

    table_body_style = ParagraphStyle(
        "TableBody",
        parent=styles["Normal"],
        fontName=FONT_REGULAR,
        fontSize=8,
        textColor=GRAY_700,
        leading=11
    )

    # --------------------------------------------------------
    # Story
    # --------------------------------------------------------

    story = []

    # ========================================================
    # COVER / TITLE
    # ========================================================

    story.append(
        Spacer(1, 10 * mm)
    )

    story.append(
        Paragraph(
            "AI Crime Investigator",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Professional AI-Assisted Investigation Report",
            subtitle_style
        )
    )

    # --------------------------------------------------------
    # Case metadata
    # --------------------------------------------------------

    generated_at = datetime.now().strftime(
        "%d %B %Y, %I:%M %p"
    )

    metadata = [
        [
            Paragraph(
                "<b>Report Generated</b>",
                table_body_style
            ),
            Paragraph(
                generated_at,
                table_body_style
            )
        ],
        [
            Paragraph(
                "<b>Investigator</b>",
                table_body_style
            ),
            Paragraph(
                safe_text(username) or "System User",
                table_body_style
            )
        ],
        [
            Paragraph(
                "<b>Start Entity</b>",
                table_body_style
            ),
            Paragraph(
                safe_text(start) or "Not specified",
                table_body_style
            )
        ],
        [
            Paragraph(
                "<b>Target Entity</b>",
                table_body_style
            ),
            Paragraph(
                safe_text(target) or "Not specified",
                table_body_style
            )
        ]
    ]

    metadata_table = Table(
        metadata,
        colWidths=[
            45 * mm,
            115 * mm
        ]
    )

    metadata_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                GRAY_50
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                GRAY_300
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                GRAY_200
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    story.append(
        metadata_table
    )

    story.append(
        Spacer(1, 8 * mm)
    )

    # ========================================================
    # EXECUTIVE SUMMARY
    # ========================================================

    story.append(
        Paragraph(
            "1. Executive Summary",
            section_style
        )
    )

    confidence_text = (
        f"{confidence}%"
        if confidence is not None
        else "Not available"
    )

    summary_text = (
        "This report presents the results of an AI-assisted "
        "crime investigation workflow. The system extracts "
        "entities and relationships from the supplied case "
        "information, constructs an investigation knowledge "
        "graph, evaluates possible paths between entities, "
        "and produces an explainable investigation summary."
    )

    story.append(
        Paragraph(
            summary_text,
            body_style
        )
    )

    # --------------------------------------------------------
    # Summary metrics
    # --------------------------------------------------------

    metric_data = [
        [
            Paragraph(
                "<b>Entities</b>",
                table_header_style
            ),
            Paragraph(
                "<b>Relationships</b>",
                table_header_style
            ),
            Paragraph(
                "<b>Confidence</b>",
                table_header_style
            ),
            Paragraph(
                "<b>Contradictions</b>",
                table_header_style
            )
        ],
        [
            Paragraph(
                str(len(entities)),
                table_body_style
            ),
            Paragraph(
                str(len(relations)),
                table_body_style
            ),
            Paragraph(
                confidence_text,
                table_body_style
            ),
            Paragraph(
                str(len(contradictions)),
                table_body_style
            )
        ]
    ]

    metric_table = Table(
        metric_data,
        colWidths=[
            40 * mm,
            40 * mm,
            40 * mm,
            40 * mm
        ]
    )

    metric_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                NAVY
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                WHITE
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                GRAY_300
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                GRAY_200
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER"
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE"
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                8
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                8
            )
        ])
    )

    story.append(
        metric_table
    )

    # ========================================================
    # CASE INPUT
    # ========================================================

    if case_text:

        story.append(
            Paragraph(
                "2. Case Information",
                section_style
            )
        )

        case_box = Table(
            [[
                Paragraph(
                    safe_text(case_text).replace(
                        "\n",
                        "<br/>"
                    ),
                    body_style
                )
            ]],
            colWidths=[160 * mm]
        )

        case_box.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    GRAY_50
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.7,
                    GRAY_300
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                )
            ])
        )

        story.append(
            case_box
        )

    # ========================================================
    # ENTITIES
    # ========================================================

    story.append(
        Paragraph(
            "3. Extracted Entities",
            section_style
        )
    )

    entity_rows = [[
        Paragraph(
            "<b>Entity</b>",
            table_header_style
        ),
        Paragraph(
            "<b>Type</b>",
            table_header_style
        )
    ]]

    for entity in entities:

        if isinstance(entity, dict):

            entity_name = (
                entity.get("text")
                or entity.get("name")
                or entity.get("id")
                or ""
            )

            entity_type = (
                entity.get("type")
                or "UNKNOWN"
            )

        else:

            entity_name = str(entity)
            entity_type = "UNKNOWN"

        entity_rows.append([
            Paragraph(
                safe_text(entity_name),
                table_body_style
            ),
            Paragraph(
                safe_text(entity_type),
                table_body_style
            )
        ])

    if len(entity_rows) == 1:

        entity_rows.append([
            Paragraph(
                "No entities extracted",
                table_body_style
            ),
            Paragraph(
                "-",
                table_body_style
            )
        ])

    entity_table = Table(
        entity_rows,
        colWidths=[
            105 * mm,
            55 * mm
        ],
        repeatRows=1
    )

    entity_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                NAVY
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [WHITE, GRAY_50]
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                GRAY_300
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                GRAY_200
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(
        entity_table
    )

    # ========================================================
    # RELATIONSHIPS
    # ========================================================

    story.append(
        Paragraph(
            "4. Investigation Relationships",
            section_style
        )
    )

    relation_rows = [[
        Paragraph(
            "<b>Source</b>",
            table_header_style
        ),
        Paragraph(
            "<b>Relationship</b>",
            table_header_style
        ),
        Paragraph(
            "<b>Target</b>",
            table_header_style
        )
    ]]

    for relation in relations:

        if not isinstance(relation, dict):
            continue

        source = relation.get(
            "source",
            ""
        )

        relation_name = relation.get(
            "relation"
            ,
            relation.get(
                "type",
                "related_to"
            )
        )

        target_name = relation.get(
            "target",
            ""
        )

        relation_rows.append([
            Paragraph(
                safe_text(source),
                table_body_style
            ),
            Paragraph(
                safe_text(relation_name),
                table_body_style
            ),
            Paragraph(
                safe_text(target_name),
                table_body_style
            )
        ])

    if len(relation_rows) == 1:

        relation_rows.append([
            Paragraph(
                "No relationships extracted",
                table_body_style
            ),
            Paragraph(
                "-",
                table_body_style
            ),
            Paragraph(
                "-",
                table_body_style
            )
        ])

    relation_table = Table(
        relation_rows,
        colWidths=[
            55 * mm,
            50 * mm,
            55 * mm
        ],
        repeatRows=1
    )

    relation_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                NAVY
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [WHITE, GRAY_50]
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                GRAY_300
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                GRAY_200
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                6
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                6
            )
        ])
    )

    story.append(
        relation_table
    )

    # ========================================================
    # GRAPH
    # ========================================================

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "5. Investigation Knowledge Graph",
            section_style
        )
    )

    story.append(
        Paragraph(
            "The graph below represents the extracted "
            "investigation entities and relationships. "
            "Different node shapes are used to distinguish "
            "persons, evidence, locations and dates.",
            body_style
        )
    )

    graph_image = generate_graph_image(
        graph_data=graph_data or {},
        relations=relations,
        entities=entities,
        start=start,
        target=target
    )

    if graph_image and graph_image.exists():

        graph_img = Image(
            str(graph_image),
            width=165 * mm,
            height=96 * mm
        )

        graph_img.hAlign = "CENTER"

        story.append(
            graph_img
        )

        story.append(
            Spacer(1, 4 * mm)
        )

        story.append(
            Paragraph(
                "Graph legend: Person = circle, Evidence = square, "
                "Location = diamond, Date = triangle. "
                "Green indicates the selected start entity and "
                "red indicates the selected target entity.",
                small_style
            )
        )

    else:

        story.append(
            Paragraph(
                "Graph could not be generated for this investigation.",
                body_style
            )
        )

    # ========================================================
    # SEARCH PATHS
    # ========================================================

    story.append(
        Paragraph(
            "6. Search Path Analysis",
            section_style
        )
    )

    def path_text(path):

        if not path:
            return "No path found"

        return " → ".join(
            safe_text(item)
            for item in path
        )

    path_rows = [
        [
            Paragraph(
                "<b>Algorithm</b>",
                table_header_style
            ),
            Paragraph(
                "<b>Result</b>",
                table_header_style
            )
        ],
        [
            Paragraph(
                "Breadth-First Search (BFS)",
                table_body_style
            ),
            Paragraph(
                path_text(bfs_path),
                table_body_style
            )
        ],
        [
            Paragraph(
                "Depth-First Search (DFS)",
                table_body_style
            ),
            Paragraph(
                path_text(dfs_path),
                table_body_style
            )
        ],
        [
            Paragraph(
                "A* Search",
                table_body_style
            ),
            Paragraph(
                path_text(astar_path),
                table_body_style
            )
        ]
    ]

    path_table = Table(
        path_rows,
        colWidths=[
            60 * mm,
            100 * mm
        ],
        repeatRows=1
    )

    path_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                NAVY
            ),
            (
                "ROWBACKGROUNDS",
                (0, 1),
                (-1, -1),
                [WHITE, GRAY_50]
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                GRAY_300
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                GRAY_200
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "TOP"
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                7
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                7
            )
        ])
    )

    story.append(
        path_table
    )

    # ========================================================
    # CONTRADICTIONS
    # ========================================================

    story.append(
        Paragraph(
            "7. Contradiction Analysis",
            section_style
        )
    )

    if contradictions:

        for contradiction in contradictions:

            story.append(
                Paragraph(
                    "• " + safe_text(
                        contradiction
                    ),
                    body_style
                )
            )

    else:

        story.append(
            Paragraph(
                "No contradictions were detected "
                "in the supplied case information.",
                body_style
            )
        )

    # ========================================================
    # EXPLANATION
    # ========================================================

    story.append(
        Paragraph(
            "8. AI Investigation Explanation",
            section_style
        )
    )

    if explanation:

        explanation_text = safe_text(
            explanation
        ).replace(
            "\n",
            "<br/>"
        )

        explanation_box = Table(
            [[
                Paragraph(
                    explanation_text,
                    body_style
                )
            ]],
            colWidths=[160 * mm]
        )

        explanation_box.setStyle(
            TableStyle([
                (
                    "BACKGROUND",
                    (0, 0),
                    (-1, -1),
                    LIGHT_BLUE
                ),
                (
                    "BOX",
                    (0, 0),
                    (-1, -1),
                    0.8,
                    BLUE
                ),
                (
                    "LEFTPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),
                (
                    "RIGHTPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),
                (
                    "TOPPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                ),
                (
                    "BOTTOMPADDING",
                    (0, 0),
                    (-1, -1),
                    10
                )
            ])
        )

        story.append(
            explanation_box
        )

    else:

        story.append(
            Paragraph(
                "No AI explanation was returned.",
                body_style
            )
        )

    # ========================================================
    # FINAL ASSESSMENT
    # ========================================================

    story.append(
        Paragraph(
            "9. Final Assessment",
            section_style
        )
    )

    final_text = (
        "The investigation result should be treated as "
        "decision-support information rather than a final "
        "legal conclusion. Extracted relationships, search "
        "paths and confidence values are dependent on the "
        "quality and completeness of the supplied evidence."
    )

    story.append(
        Paragraph(
            final_text,
            body_style
        )
    )

    # ========================================================
    # DISCLAIMER
    # ========================================================

    disclaimer = Table(
        [[
            Paragraph(
                "<b>Important:</b> This report is generated "
                "using an AI-assisted investigation workflow. "
                "Human investigators should validate all "
                "evidence, relationships and conclusions "
                "before taking operational or legal action.",
                small_style
            )
        ]],
        colWidths=[160 * mm]
    )

    disclaimer.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                LIGHT_ORANGE
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                ORANGE
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                10
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                10
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                9
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                9
            )
        ])
    )

    story.append(
        Spacer(1, 6 * mm)
    )

    story.append(
        disclaimer
    )

    # ========================================================
    # BUILD PDF
    # ========================================================

    doc.build(
        story,
        onFirstPage=draw_header_footer,
        onLaterPages=draw_header_footer
    )

    return str(pdf_path)


# ============================================================
# BACKWARD COMPATIBILITY
# ============================================================

def generate_report(
    case_text,
    entities,
    relations,
    search_results=None,
    confidence=0,
    contradictions=None,
    **kwargs
):
    return generate_pdf_report(
        entities=entities,
        relations=relations,
        confidence=confidence,
        contradictions=contradictions,
        case_text=case_text,
        **kwargs
    )


def create_pdf_report(*args, **kwargs):
    return generate_report(
        *args,
        **kwargs
    )