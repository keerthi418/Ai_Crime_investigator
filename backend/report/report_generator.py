from reportlab.lib.pagesizes import A4
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_CENTER
from pathlib import Path
from datetime import datetime


def generate_report(
    case_text,
    entities,
    relations,
    search_results,
    confidence,
    contradictions
):

    reports_folder = Path("reports")
    reports_folder.mkdir(exist_ok=True)

    filename = (
        reports_folder /
        f"crime_investigation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    )

    document = SimpleDocTemplate(
        str(filename),
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = styles["Title"]
    title_style.alignment = TA_CENTER

    story = []

    story.append(
        Paragraph(
            "AI CRIME INVESTIGATOR",
            title_style
        )
    )

    story.append(
        Paragraph(
            "Explainable Investigation Report",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"<b>Generated:</b> "
            f"{datetime.now().strftime('%d-%m-%Y %H:%M:%S')}",
            styles["Normal"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "<b>CASE DESCRIPTION</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            case_text,
            styles["BodyText"]
        )
    )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "<b>EXTRACTED ENTITIES</b>",
            styles["Heading2"]
        )
    )

    entity_data = [["Entity", "Type"]]

    for entity in entities:
        entity_data.append([
            entity["text"],
            entity["type"]
        ])

    entity_table = Table(entity_data)

    entity_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(entity_table)

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "<b>RELATIONSHIPS</b>",
            styles["Heading2"]
        )
    )

    relation_data = [["Source", "Relationship", "Target"]]

    for relation in relations:

        relation_data.append([
            relation["source"],
            relation["relation"],
            relation["target"]
        ])

    relation_table = Table(relation_data)

    relation_table.setStyle(
        TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("PADDING", (0, 0), (-1, -1), 6)
        ])
    )

    story.append(relation_table)

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "<b>SEARCH ANALYSIS</b>",
            styles["Heading2"]
        )
    )

    for algorithm, path in search_results.items():

        path_text = " → ".join(path) if path else "No path found"

        story.append(
            Paragraph(
                f"<b>{algorithm}:</b> {path_text}",
                styles["BodyText"]
            )
        )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            f"<b>BAYESIAN CONFIDENCE:</b> "
            f"{confidence * 100:.1f}%",
            styles["Heading2"]
        )
    )

    story.append(Spacer(1, 10))

    story.append(
        Paragraph(
            "<b>CONTRADICTIONS</b>",
            styles["Heading2"]
        )
    )

    if contradictions:

        for contradiction in contradictions:

            story.append(
                Paragraph(
                    f"⚠ {contradiction}",
                    styles["BodyText"]
                )
            )

    else:

        story.append(
            Paragraph(
                "No major contradictions detected.",
                styles["BodyText"]
            )
        )

    story.append(Spacer(1, 15))

    story.append(
        Paragraph(
            "<b>EXPLAINABLE AI SUMMARY</b>",
            styles["Heading2"]
        )
    )

    story.append(
        Paragraph(
            "The investigation result is based on extracted entities, "
            "relationships, graph search results, evidence confidence, "
            "and detected contradictions.",
            styles["BodyText"]
        )
    )

    document.build(story)

    return str(filename)