from pathlib import Path
from datetime import datetime
import html
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


# ============================================================
# DIRECTORIES
# ============================================================

BASE_DIR = Path(__file__).resolve().parents[2]

REPORTS_DIR = BASE_DIR / "reports"
REPORTS_DIR.mkdir(parents=True, exist_ok=True)


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
    Use Arial when available on Windows.
    Otherwise fall back to Helvetica.
    """

    windows_fonts = Path("C:/Windows/Fonts")

    regular = windows_fonts / "arial.ttf"
    bold = windows_fonts / "arialbd.ttf"
    italic = windows_fonts / "ariali.ttf"

    if regular.exists() and bold.exists():

        try:

            pdfmetrics.registerFont(
                TTFont(
                    "ArialCustom",
                    str(regular)
                )
            )

            pdfmetrics.registerFont(
                TTFont(
                    "ArialCustom-Bold",
                    str(bold)
                )
            )

            if italic.exists():

                pdfmetrics.registerFont(
                    TTFont(
                        "ArialCustom-Italic",
                        str(italic)
                    )
                )

            return (
                "ArialCustom",
                "ArialCustom-Bold"
            )

        except Exception:
            pass

    return (
        "Helvetica",
        "Helvetica-Bold"
    )


FONT_REGULAR, FONT_BOLD = register_fonts()


# ============================================================
# SAFE TEXT
# ============================================================

def safe_text(value):
    """
    Convert any value to safe ReportLab HTML text.
    """

    if value is None:
        return ""

    return html.escape(str(value))


# ============================================================
# TEXT WRAPPING
# ============================================================

def wrap_text(text, width=110):

    if text is None:
        return ""

    text = str(text)

    if not text:
        return ""

    return "\n".join(
        textwrap.wrap(
            text,
            width=width,
            break_long_words=True,
            break_on_hyphens=False
        )
    )


# ============================================================
# HEADER / FOOTER
# ============================================================

def draw_header_footer(canvas, doc):

    canvas.saveState()

    width, height = A4

    # --------------------------------------------------------
    # HEADER LINE
    # --------------------------------------------------------

    canvas.setStrokeColor(BLUE)
    canvas.setLineWidth(1.2)

    canvas.line(
        18 * mm,
        height - 16 * mm,
        width - 18 * mm,
        height - 16 * mm
    )

    # --------------------------------------------------------
    # HEADER TITLE
    # --------------------------------------------------------

    canvas.setFont(
        FONT_BOLD,
        8
    )

    canvas.setFillColor(NAVY)

    canvas.drawString(
        18 * mm,
        height - 12 * mm,
        "AI CRIME INVESTIGATOR"
    )

    # --------------------------------------------------------
    # HEADER RIGHT
    # --------------------------------------------------------

    canvas.setFont(
        FONT_REGULAR,
        7
    )

    canvas.setFillColor(GRAY_500)

    canvas.drawRightString(
        width - 18 * mm,
        height - 12 * mm,
        "AI-Assisted Investigation Report"
    )

    # --------------------------------------------------------
    # FOOTER LINE
    # --------------------------------------------------------

    canvas.setStrokeColor(GRAY_300)
    canvas.setLineWidth(0.5)

    canvas.line(
        18 * mm,
        15 * mm,
        width - 18 * mm,
        15 * mm
    )

    # --------------------------------------------------------
    # FOOTER LEFT
    # --------------------------------------------------------

    canvas.setFont(
        FONT_REGULAR,
        7
    )

    canvas.setFillColor(GRAY_500)

    canvas.drawString(
        18 * mm,
        9 * mm,
        "Confidential Investigation Report"
    )

    # --------------------------------------------------------
    # FOOTER PAGE NUMBER
    # --------------------------------------------------------

    canvas.drawRightString(
        width - 18 * mm,
        9 * mm,
        f"Page {doc.page}"
    )

    canvas.restoreState()


# ============================================================
# GRAPH GENERATOR
# ============================================================

def generate_graph_image(
    graph_data=None,
    relations=None,
    entities=None,
    start=None,
    target=None
):

    relations = relations or []
    entities = entities or []
    graph_data = graph_data or {}

    graph = nx.DiGraph()

    # ========================================================
    # ADD ENTITIES
    # ========================================================

    for entity in entities:

        if isinstance(entity, dict):

            name = (
                entity.get("text")
                or entity.get("name")
                or entity.get("id")
            )

            entity_type = (
                entity.get("type")
                or entity.get("entity_type")
                or "PERSON"
            )

        else:

            name = str(entity)
            entity_type = "PERSON"

        if name:

            graph.add_node(
                str(name),
                entity_type=str(
                    entity_type
                ).upper()
            )

    # ========================================================
    # ADD GRAPH NODES
    # ========================================================

    if isinstance(graph_data, dict):

        nodes = graph_data.get(
            "nodes",
            []
        )

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
                    entity_type=str(
                        node_type
                    ).upper()
                )

    # ========================================================
    # ADD RELATIONS
    # ========================================================

    for relation in relations:

        if not isinstance(relation, dict):
            continue

        source = (
            relation.get("source")
            or relation.get("from")
        )

        target_node = (
            relation.get("target")
            or relation.get("to")
        )

        relation_name = (
            relation.get("relation")
            or relation.get("label")
            or relation.get("type")
            or "related_to"
        )

        if not source or not target_node:
            continue

        source = str(source)
        target_node = str(target_node)

        if source not in graph.nodes:

            graph.add_node(
                source,
                entity_type="PERSON"
            )

        if target_node not in graph.nodes:

            graph.add_node(
                target_node,
                entity_type="PERSON"
            )

        graph.add_edge(
            source,
            target_node,
            relation=str(relation_name)
        )

    # ========================================================
    # GRAPH DATA EDGES
    # ========================================================

    if isinstance(graph_data, dict):

        edges = graph_data.get(
            "edges",
            []
        )

        for edge in edges:

            if not isinstance(edge, dict):
                continue

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

            if source and target_node:

                graph.add_edge(
                    str(source),
                    str(target_node),
                    relation=str(
                        relation_name
                    )
                )

    # ========================================================
    # EMPTY GRAPH
    # ========================================================

    if len(graph.nodes) == 0:
        return None

    # ========================================================
    # FIGURE
    # ========================================================

    fig = plt.figure(
        figsize=(12, 7),
        dpi=180
    )

    ax = fig.add_subplot(111)

    ax.set_facecolor("#F8FAFC")

    # ========================================================
    # GRAPH LAYOUT
    # ========================================================

    try:

        node_count = len(
            graph.nodes
        )

        if node_count <= 3:

            pos = nx.spring_layout(
                graph,
                seed=42,
                k=2.5
            )

        elif node_count <= 10:

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

    # ========================================================
    # NODE GROUPS
    # ========================================================

    person_nodes = []
    evidence_nodes = []
    location_nodes = []
    date_nodes = []
    other_nodes = []

    for node, data in graph.nodes(
        data=True
    ):

        node_type = str(
            data.get(
                "entity_type",
                "PERSON"
            )
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

    # ========================================================
    # PERSON
    # ========================================================

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

    # ========================================================
    # EVIDENCE
    # ========================================================

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

    # ========================================================
    # LOCATION
    # ========================================================

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

    # ========================================================
    # DATE
    # ========================================================

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

    # ========================================================
    # OTHER
    # ========================================================

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

    # ========================================================
    # START NODE
    # ========================================================

    if start:

        start = str(start)

        if start in graph.nodes:

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

    # ========================================================
    # TARGET NODE
    # ========================================================

    if target:

        target = str(target)

        if target in graph.nodes:

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

    # ========================================================
    # EDGES
    # ========================================================

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

    # ========================================================
    # NODE LABELS
    # ========================================================

    labels = {}

    for node in graph.nodes:

        node_text = str(node)

        if len(node_text) > 22:

            node_text = (
                node_text[:19]
                + "..."
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

    # ========================================================
    # EDGE LABELS
    # ========================================================

    edge_labels = {}

    for (
        source,
        target_node,
        data
    ) in graph.edges(
        data=True
    ):

        relation_name = data.get(
            "relation",
            "related_to"
        )

        edge_labels[
            (source, target_node)
        ] = str(relation_name)

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

    # ========================================================
    # TITLE
    # ========================================================

    ax.set_title(
        "Investigation Knowledge Graph",
        fontsize=15,
        fontweight="bold",
        color="#0F172A",
        pad=18
    )

    # ========================================================
    # LEGEND
    # ========================================================

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

    # ========================================================
    # SAVE IMAGE
    # ========================================================

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
# PDF REPORT
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
    search_results=None,
    **kwargs
):

    entities = entities or []
    relations = relations or []
    bfs_path = bfs_path or []
    dfs_path = dfs_path or []
    astar_path = astar_path or []
    contradictions = contradictions or []
    search_results = search_results or {}

    # ========================================================
    # PDF FILE
    # ========================================================

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    pdf_path = (
        REPORTS_DIR
        / f"crime_investigation_{timestamp}.pdf"
    )

    # ========================================================
    # DOCUMENT
    # ========================================================

    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,

        # Professional margins
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=24 * mm,
        bottomMargin=22 * mm,

        title="AI Crime Investigator Report",
        author="AI Crime Investigator",
        subject="AI-assisted crime investigation report",

        # Prevent accidental overflow
        allowSplitting=1
    )

    styles = getSampleStyleSheet()

    # ========================================================
    # STYLES
    # ========================================================

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

    pass_status_style = ParagraphStyle(
        "PassStatus",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9,
        textColor=GREEN
    )

    fail_status_style = ParagraphStyle(
        "FailStatus",
        parent=styles["Normal"],
        fontName=FONT_BOLD,
        fontSize=9,
        textColor=RED
    )

    sub_section_style = ParagraphStyle(
        "SubSection",
        parent=styles["Heading3"],
        fontName=FONT_BOLD,
        fontSize=10.5,
        leading=14,
        textColor=GRAY_700,
        spaceBefore=10,
        spaceAfter=5
    )

    # ========================================================
    # STORY
    # ========================================================

    story = []

    # ========================================================
    # TITLE
    # ========================================================

    story.append(
        Spacer(
            1,
            10 * mm
        )
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

    # ========================================================
    # METADATA
    # ========================================================

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
                safe_text(generated_at),
                table_body_style
            )
        ],

        [
            Paragraph(
                "<b>Investigator</b>",
                table_body_style
            ),
            Paragraph(
                safe_text(username)
                or "System User",
                table_body_style
            )
        ],

        [
            Paragraph(
                "<b>Start Entity</b>",
                table_body_style
            ),
            Paragraph(
                safe_text(start)
                or "Not specified",
                table_body_style
            )
        ],

        [
            Paragraph(
                "<b>Target Entity</b>",
                table_body_style
            ),
            Paragraph(
                safe_text(target)
                or "Not specified",
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
        Spacer(
            1,
            8 * mm
        )
    )

    # ========================================================
    # 1. EXECUTIVE SUMMARY
    # ========================================================

    story.append(
        Paragraph(
            "1. Executive Summary",
            section_style
        )
    )

    if confidence is not None:

        try:

            confidence_number = float(
                confidence
            )

            # Confidence is stored as a 0.0-1.0 score.  Convert it
            # to a percentage here so the PDF shows the SAME value
            # as the UI (e.g. 0.9 -> "90%", never "0.9%").
            if 0.0 <= confidence_number <= 1.0:
                confidence_number = (
                    confidence_number * 100
                )

            confidence_text = (
                f"{confidence_number:.1f}%"
            )

        except Exception:

            confidence_text = (
                safe_text(confidence)
            )

    else:

        confidence_text = "Not available"

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

    # ========================================================
    # SUMMARY METRICS
    # ========================================================

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
    # 2. CASE INFORMATION
    # ========================================================

    if case_text:

        story.append(
            Paragraph(
                "2. Case Information",
                section_style
            )
        )

        case_text_html = safe_text(
            case_text
        ).replace(
            "\n",
            "<br/>"
        )

        case_box = Table(
            [[
                Paragraph(
                    case_text_html,
                    body_style
                )
            ]],
            colWidths=[
                160 * mm
            ]
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
    # 3. ENTITIES
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
                or entity.get("entity_type")
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
    # 4. RELATIONSHIPS
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

        source = (
            relation.get("source")
            or relation.get("from")
            or ""
        )

        relation_name = (
            relation.get("relation")
            or relation.get("label")
            or relation.get("type")
            or "related_to"
        )

        target_name = (
            relation.get("target")
            or relation.get("to")
            or ""
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
    # 5. KNOWLEDGE GRAPH
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
            "Different node shapes distinguish persons, "
            "evidence, locations and dates.",
            body_style
        )
    )

    graph_image = generate_graph_image(
        graph_data=graph_data,
        relations=relations,
        entities=entities,
        start=start,
        target=target
    )

    if graph_image and graph_image.exists():

        graph_img = Image(
            str(graph_image),
            width=160 * mm,
            height=90 * mm
        )

        graph_img.hAlign = "CENTER"

        story.append(
            graph_img
        )

        story.append(
            Spacer(
                1,
                4 * mm
            )
        )

        story.append(
            Paragraph(
                "Graph legend: Person = circle, "
                "Evidence = square, Location = diamond, "
                "Date = triangle. Green indicates the "
                "selected start entity and red indicates "
                "the selected target entity.",
                small_style
            )
        )

    else:

        story.append(
            Paragraph(
                "Graph could not be generated for "
                "this investigation.",
                body_style
            )
        )

    # ========================================================
    # 6. SEARCH PATH ANALYSIS
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

    # The PDF shows the EXACT search_results structure the UI
    # displays.  search_results is the single source of truth; the
    # individually-passed bfs/dfs/astar lists are only a fallback.
    def _search_path(label, fallback):

        detail = search_results.get(label)

        if isinstance(detail, dict):
            detail_path = detail.get("path")
            if detail_path:
                return detail_path

        return fallback

    # Per-algorithm result block:
    #
    #     Start:  Arun Kumar
    #     Target: Ravi
    #     Status: PATH FOUND
    #     Path:   Arun Kumar → [transferred_to] → Ravi
    #     Length: 1
    #
    # Relation labels are taken from search_results.<label>.edges,
    # which graph_store derives from the REAL NetworkX edges.
    def _algorithm_block(label, fallback):

        detail = search_results.get(label)

        if not isinstance(detail, dict):
            detail = {}

        path = _search_path(label, fallback)

        found = bool(path)

        length = int(
            detail.get(
                "length",
                detail.get(
                    "path_length",
                    max(0, len(path) - 1) if path else 0,
                ),
            )
            or 0
        )

        edges = detail.get("edges") or []

        if edges and len(path) > 1:

            labeled = "".join(
                (
                    str(edge.get("source", ""))
                    if index == 0
                    else ""
                )
                + " → ["
                + str(
                    edge.get(
                        "relation",
                        "related_to",
                    )
                )
                + "] → "
                + str(edge.get("target", ""))
                for index, edge
                in enumerate(edges)
            )

        else:

            labeled = path_text(path)

        report_start = (
            search_results.get("start")
            or start
            or "—"
        )

        report_target = (
            search_results.get("target")
            or target
            or "—"
        )

        status = (
            "PATH FOUND"
            if found
            else "NO PATH FOUND"
        )

        return Paragraph(
            "<b>Start:</b> "
            + safe_text(report_start)
            + "<br/>"
            + "<b>Target:</b> "
            + safe_text(report_target)
            + "<br/>"
            + "<b>Status:</b> "
            + status
            + "<br/>"
            + "<b>Path:</b> "
            + safe_text(labeled)
            + "<br/>"
            + "<b>Length:</b> "
            + str(length),
            table_body_style,
        )

    path_rows = [

        [
            Paragraph(
                "<b>Algorithm</b>",
                table_header_style
            ),

            Paragraph(
                "<b>Start → Target (relation-aware)</b>",
                table_header_style
            )
        ],

        [
            Paragraph(
                "Breadth-First Search (BFS)",
                table_body_style
            ),

            _algorithm_block("BFS", bfs_path)
        ],

        [
            Paragraph(
                "Depth-First Search (DFS)",
                table_body_style
            ),

            _algorithm_block("DFS", dfs_path)
        ],

        [
            Paragraph(
                "A* Search",
                table_body_style
            ),

            _algorithm_block("A*", astar_path)
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

    # --------------------------------------------------------
    # ALGORITHM VERIFICATION METRICS (BFS / DFS / A*)
    # --------------------------------------------------------
    #
    # Each algorithm is graded PASS/FAIL. A candidate path
    # produced by the algorithm must actually connect the
    # start and target nodes in the reported order and be
    # shorter than (A*) / equal to the length of an obvious
    # direct relationship; otherwise the algorithm is marked
    # FAIL with a reason.

    def _get_detail(search_results, key):

        detail = search_results.get(key)

        if not isinstance(detail, dict):
            return {}

        return detail

    def _note(text):
        return (
            "—"
            if not text
            else safe_text(text)
        )

    detail_bfs = _get_detail(
        search_results,
        "BFS"
    )

    detail_dfs = _get_detail(
        search_results,
        "DFS"
    )

    detail_astar = _get_detail(
        search_results,
        "A*"
    )

    metric_rows = [
        [
            Paragraph(
                "<b>Algorithm</b>",
                table_header_style
            ),
            Paragraph(
                "<b>Status</b>",
                table_header_style
            ),
            Paragraph(
                "<b>Found</b>",
                table_header_style
            ),
            Paragraph(
                "<b>Path Length</b>",
                table_header_style
            ),
            Paragraph(
                "<b>Visited</b>",
                table_header_style
            ),
            Paragraph(
                "<b>Time (ms)</b>",
                table_header_style
            )
        ]
    ]

    for label, detail, fallback_path in (
        ("BFS", detail_bfs, bfs_path),
        ("DFS", detail_dfs, dfs_path),
        ("A*", detail_astar, astar_path),
    ):

        found = bool(
            detail.get("found")
            if detail
            else fallback_path
        )

        path_length = int(
            detail.get(
                "path_length",
                0,
            )
            if detail
            else len(fallback_path)
        )

        visited = int(
            detail.get(
                "visited_nodes",
                0,
            )
            if detail
            else 0
        )

        execution_ms = float(
            detail.get(
                "execution_time_ms",
                0,
            )
            if detail
            else 0
        )

        status_text = (
            "PASS"
            if found
            else "FAIL"
        )

        status_style = (
            pass_status_style
            if found
            else fail_status_style
        )

        metric_rows.append(
            [
                Paragraph(
                    f"<b>{label}</b>",
                    table_body_style
                ),
                Paragraph(
                    status_text,
                    status_style
                ),
                Paragraph(
                    "Yes"
                    if found
                    else "No",
                    table_body_style
                ),
                Paragraph(
                    str(path_length),
                    table_body_style
                ),
                Paragraph(
                    str(visited),
                    table_body_style
                ),
                Paragraph(
                    f"{execution_ms:.4f}",
                    table_body_style
                )
            ]
        )

    # Extra A* columns (cost + heuristic).
    metric_rows.append(
        [
            Paragraph(
                "Note",
                table_body_style
            ),
            Paragraph(
                "—",
                table_body_style
            ),
            Paragraph(
                "—",
                table_body_style
            ),
            Paragraph(
                "—",
                table_body_style
            ),
            Paragraph(
                "—",
                table_body_style
            ),
            Paragraph(
                "—",
                table_body_style
            )
        ]
    )

    metric_rows[-1] = [
        Paragraph(
            "<b>A* Cost</b>",
            table_body_style
        ),
        Paragraph(
            "—",
            table_body_style
        ),
        Paragraph(
            "—",
            table_body_style
        ),
        Paragraph(
            str(
                int(
                    detail_astar.get(
                        "cost",
                        0,
                    )
                    if detail_astar
                    else 0
                )
            ),
            table_body_style
        ),
        Paragraph(
            "—",
            table_body_style
        ),
        Paragraph(
            _note(
                detail_astar.get(
                    "heuristic_used",
                )
                if detail_astar
                else None
            ),
            table_body_style
        )
    ]

    metric_table = Table(
        metric_rows,
        colWidths=[
            26 * mm,
            28 * mm,
            18 * mm,
            24 * mm,
            20 * mm,
            42 * mm
        ],
        repeatRows=1
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
        Paragraph(
            "Algorithm Verification (PASS/FAIL)",
            sub_section_style
        )
    )

    story.append(
        metric_table
    )

    # ========================================================
    # 7. CONTRADICTION ANALYSIS
    # ========================================================

    story.append(
        Paragraph(
            "7. Contradiction Analysis",
            section_style
        )
    )

    if contradictions:

        for contradiction in contradictions:

            if isinstance(contradiction, dict):

                contra_type = str(
                    contradiction.get("type", "contradiction")
                ).replace("_", " ").strip()

                severity = str(
                    contradiction.get("severity", "")
                ).strip().upper()

                message = (
                    contradiction.get("message")
                    or contradiction.get("claim")
                    or ""
                )

                heading = (
                    f"• {contra_type.title()} "
                    f"[{severity}]: {message}"
                    if severity
                    else f"• {contra_type.title()}: {message}"
                )

                story.append(
                    Paragraph(
                        safe_text(heading),
                        body_style
                    )
                )

                claim_text = safe_text(
                    contradiction.get("claim") or ""
                )

                evidence_text = safe_text(
                    contradiction.get("evidence") or ""
                )

                if claim_text:
                    story.append(
                        Paragraph(
                            "Claim: " + claim_text,
                            body_style
                        )
                    )

                if evidence_text:
                    story.append(
                        Paragraph(
                            "Evidence: " + evidence_text,
                            body_style
                        )
                    )

            else:

                contradiction_text = safe_text(
                    contradiction
                )

                story.append(
                    Paragraph(
                        "• " + contradiction_text,
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
    # 8. AI EXPLANATION
    # ========================================================

    story.append(
        Paragraph(
            "8. AI Investigation Explanation",
            section_style
        )
    )

    if explanation:

        # The explanation may be a list of statements
        # (one per identified factor) or a plain string.
        if isinstance(explanation, list):

            explanation_text = (
                "<br/>".join(
                    safe_text(
                        str(item)
                    )
                    for item in explanation
                )
            )

        else:

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
            colWidths=[
                160 * mm
            ]
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
    # 9. FINAL ASSESSMENT
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
        "paths and confidence values depend on the quality "
        "and completeness of the supplied evidence."
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
        colWidths=[
            160 * mm
        ]
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
        Spacer(
            1,
            6 * mm
        )
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

    # ========================================================
    # CLEAN GRAPH IMAGE
    # ========================================================

    try:

        if graph_image and graph_image.exists():

            graph_image.unlink()

    except Exception:

        pass

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
        search_results=search_results or {},
        **kwargs
    )


def create_pdf_report(
    *args,
    **kwargs
):

    return generate_report(
        *args,
        **kwargs
    )