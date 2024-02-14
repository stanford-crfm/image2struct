from typing import List, Dict

TEX_DELIMITERS: Dict[str, List[List[str]]] = {
    "equation": (
        None,
        [
            ["\\begin{equation}", "\\end{equation}"],
            ["\\begin{equation*}", "\\end{equation*}"],
            ["\\begin{align}", "\\end{align}"],
            ["\\begin{align*}", "\\end{align*}"],
            ["\\begin{multline}", "\\end{multline}"],
            ["\\begin{multline*}", "\\end{multline*}"],
            ["\\begin{gather}", "\\end{gather}"],
            ["\\begin{gather*}", "\\end{gather*}"],
            ["\\begin{flalign}", "\\end{flalign}"],
            ["\\begin{flalign*}", "\\end{flalign*}"],
            ["\\begin{alignat}", "\\end{alignat}"],
            ["\\begin{alignat*}", "\\end{alignat*}"],
            ["\\begin{aligneq}", "\\end{aligneq}"],
            ["\\begin{aligneq*}", "\\end{aligneq*}"],
            ["\\begin{subequations}", "\\end{subequations}"],
            ["\\begin{subequations*}", "\\end{subequations*}"],
            ["\\begin{subeqnarray}", "\\end{subeqnarray}"],
            ["\\begin{subeqnarray*}", "\\end{subeqnarray*}"],
            ["\\begin{math}", "\\end{math}"],
            ["\\begin{displaymath}", "\\end{displaymath}"],
        ],
    ),
    "figure": (
        "\\includegraphics",
        [
            ["\\begin{figure}", "\\end{figure}"],
            ["\\begin{figure*}", "\\end{figure*}"],
            ["\\begin{wrapfigure}", "\\end{wrapfigure}"],
            ["\\begin{wrapfigure*}", "\\end{wrapfigure*}"],
            ["\\begin{sidewaysfigure}", "\\end{sidewaysfigure}"],
            ["\\begin{sidewaysfigure*}", "\\end{sidewaysfigure*}"],
            ["\\begin{minipage}", "\\end{minipage}"],
            ["\\begin{minipage*}", "\\end{minipage*}"],
            ["\\begin{tabular}", "\\end{tabular}"],
            ["\\begin{tabular*}", "\\end{tabular*}"],
            ["\\begin{tabularx}", "\\end{tabularx}"],
        ],
    ),
    "table": (
        None,
        [
            ["\\begin{table}", "\\end{table}"],
            ["\\begin{table*}", "\\end{table*}"],
            ["\\begin{tabbing}", "\\end{tabbing}"],
        ],
    ),
    "algorithm": (
        None,
        [
            ["\\begin{algorithm}", "\\end{algorithm}"],
            ["\\begin{algorithmic}", "\\end{algorithmic}"],
            ["\\begin{algorithmic*}", "\\end{algorithmic*}"],
        ],
    ),
    "plot": (
        None,
        [
            ["\\begin{tikzpicture}", "\\end{tikzpicture}"],
            ["\\begin{tikzcd}", "\\end{tikzcd}"],
            ["\\begin{tikzcd*}", "\\end{tikzcd*}"],
        ],
    ),
}


TEX_BEGIN = r"""
\documentclass{article}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{graphicx}
\usepackage{graphicx}
\usepackage{amsmath}
\usepackage{xcolor}
\usepackage{algorithm}
\usepackage{algpseudocode}
\usepackage{stfloats}
\usepackage{epstopdf}
\usepackage{pgfplots}
\begin{document}"""

TEX_END = r"""\end{document}"""
