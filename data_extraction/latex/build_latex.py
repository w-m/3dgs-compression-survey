import os
import subprocess
from pathlib import Path

methodsdir = "../../methods"
imagedir = "../../project-page/static/images/"

# List of markdown files to combine
markdown_files = os.listdir(methodsdir)
image_files = os.listdir(imagedir)

# Combined markdown content
combined_markdown = ""
section_count = 1

with open("tex_templates/preamble.tex", "r") as file:
    tex_preamble = file.read()

with open("tex_templates/end_document.tex", "r") as file:
    tex_end_document = file.read()

with open("tex_templates/figure.tex", "r") as file:
    tex_figure = file.read()

with open("tex_templates/entry.tex", "r") as file:
    tex_entry = file.read()


def extract_title_and_text(markdown: str):
    markdown = markdown.strip()
    lines = markdown.split("\n")
    assert lines[0].startswith("#")
    # We assume that there are no hashtags in the title.
    # Who puts hashtags in a title anyway?
    title = lines[0].replace("#", "").strip()
    text = "\n".join(lines[1:]).strip()
    return title, text


def generate_section(paper_title: str, paper_text: str, paper_id: str, figure: str):
    global tex_entry
    section = tex_entry.replace("<paper_title>", paper_title)
    section = section.replace("<paper_text>", paper_text)
    section = section.replace("<paper_id>", paper_id)
    section = section.replace("<figure>", figure)
    return section


tex_content = ""
for filename in markdown_files:
    with open(os.path.join(methodsdir, filename), "r") as file:
        title, text = extract_title_and_text(file.read())
        paper_id = Path(filename).stem
        image_name = paper_id + ".png"
        image_path = os.path.join(imagedir, image_name)

        figure_template = tex_figure.replace("<image_path>", image_path)
        latex_section = generate_section(title, text, paper_id, figure_template)
        tex_content += "\n\n" + latex_section

full_document = tex_preamble + tex_content + tex_end_document

with open("3dgs_compression_survey.tex", "w") as file:
    file.write(full_document)

# Step 4: Compile LaTeX Document
subprocess.run(["pdflatex", "3dgs_compression_survey.tex"])
subprocess.run(["bibtex", "3dgs_compression_survey"])
subprocess.run(["pdflatex", "3dgs_compression_survey.tex"])
subprocess.run(["pdflatex", "3dgs_compression_survey.tex"])
subprocess.run(["open", "3dgs_compression_survey.pdf"])

subprocess.run(
    [
        "rm",
        "3dgs_compression_survey.aux",
        "3dgs_compression_survey.bbl",
        "3dgs_compression_survey.blg",
        "3dgs_compression_survey.log",
        "3dgs_compression_survey.out",
    ]
)
