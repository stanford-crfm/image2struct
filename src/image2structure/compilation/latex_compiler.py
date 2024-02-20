from typing import Any, Dict, Optional, Tuple, List
from latex import build_pdf
from PIL import Image

import os
import io
import tarfile
import shutil
import re
import numpy as np
import random

from image2structure.compilation.compiler import Compiler, CompilationError
from image2structure.compilation.utils import pdf_to_image
from image2structure.compilation.tex.constants import (
    TEX_DELIMITERS,
    TEX_BEGIN,
    TEX_END,
)


class LatexCompiler(Compiler):

    CATEGORIES: List[str] = ["equation", "table", "figure", "algorithm", "plot"]

    def __init__(
        self,
        crop: bool,
        num_instances: int,
        max_elt_per_category: int,
        verbose: bool = False,
        categories: List[str] = CATEGORIES,
    ):
        self._crop = crop
        self._verbose = verbose
        self._categories = categories

        # Counter to save the assets
        self._asset_number = 0

        # Internal counter fo all categories (equations, tables, figures, ...)
        self._max_elt_per_category = max_elt_per_category
        self._num_instances = num_instances
        self._num_to_do: Dict[str, int] = {
            category: num_instances for category in categories
        }

    @staticmethod
    def latex_to_pdf(latex_code: str, assets_path: str) -> io.BytesIO:
        """Convert a LaTeX code to a PDF.

        Args:
            latex_code: The LaTeX code.
            assets_path: The path to the assets.

        Returns:
            io.BytesIO: The PDF as a byte stream.
        """
        # Compiling LaTeX code to PDF
        path = os.path.join(os.path.abspath(os.path.dirname(__file__)), assets_path)
        pdf = build_pdf(latex_code, texinputs=[path, ""])
        return io.BytesIO(pdf.data)  # Convert PDF to a byte stream

    @staticmethod
    def latex_to_image(
        latex_code: str,
        assets_path: str,
        crop: bool = False,
        resize_to: Optional[Tuple[int, int]] = None,
    ) -> Tuple[Optional[Image.Image], Tuple[int, int]]:
        """Convert a LaTeX code to an image.

        Args:
            latex_code: The LaTeX code.
            assets_path: The path to the assets.
            crop: Whether to crop the image to remove the white border.
            resize_to: The size to resize the image to.

        Returns:
            Optional[Image.Image]: The image (will be None if the conversion failed).
            Tuple[int, int]: The size of the image, (0, 0) if the conversion failed.
        """
        try:
            pdf_stream = LatexCompiler.latex_to_pdf(latex_code, assets_path=assets_path)
            image = pdf_to_image(pdf_stream, crop=crop, resize_to=resize_to)
            return image, image.size
        except Exception:
            return None, (0, 0)

    @staticmethod
    def get_asset_names_used(latex_code: str) -> List[str]:
        """Extract the names of the assets used in the LaTeX code.

        Args:
            latex_code: The LaTeX code.

        Returns:
            List[str]: The names of the assets used in the LaTeX code.
        """
        pattern = r"\\includegraphics(?:\[[^\]]+\])?\{([^}]+)\}"
        asset_names = re.findall(pattern, latex_code)
        return asset_names

    def rename_and_save_assets(
        self, latex_code: str, src_path: str, dest_path: str
    ) -> str:
        """Given a LaTeX code, rename and save the assets used in the code.
        Returns the new LaTeX code with the renamed assets.

        Args:
            latex_code: The LaTeX code.
            src_path: The path to the source directory.
            dest_path: The path to the destination directory.

        Returns:
            str: The new LaTeX code with the renamed assets.
        """
        asset_names: List[str] = LatexCompiler.get_asset_names_used(latex_code)
        # Associates the new path to [tex_name, original_path]
        asset_mapping: Dict[str, List[str]] = {}

        # Rename the assets by replacing / by _ and adding num_extracted _ at the beginning
        for original_name in asset_names:
            original_name_with_extension = original_name
            if "." not in original_name_with_extension:
                # Find a file starting with the original_name to determine the extension
                file_name = original_name_with_extension.split("/")[-1]
                asset_dest = os.path.join(
                    src_path, "/".join(original_name_with_extension.split("/")[:-1])
                )
                for _, _, files in os.walk(asset_dest):
                    for file in files:
                        if file.startswith(file_name):
                            extension = os.path.splitext(file)[1]
                            original_name_with_extension += extension
                            break
            new_name = (
                f'{self._asset_number}_{original_name_with_extension.replace("/", "_")}'
            )
            asset_mapping[new_name] = [original_name, original_name_with_extension]
            self._asset_number += 1

        # Replace the occurences in the tex_code
        for new_name, [original_name, _] in asset_mapping.items():
            latex_code = latex_code.replace(original_name, new_name)

        # Move the assets
        for new_name, [_, original_name_with_extension] in asset_mapping.items():
            asset_path = os.path.join(src_path, original_name_with_extension)
            new_asset_path = os.path.join(dest_path, new_name)
            try:
                shutil.copy(asset_path, new_asset_path)
            except FileNotFoundError:
                pass

        return latex_code

    @staticmethod
    def read_latex_file(path: str) -> Tuple[Optional[str], bool]:
        """Read the content of a LaTeX file.

        Args:
            path: The path to the LaTeX file.

        Returns:
            Optional[str]: The content of the LaTeX file.
            bool: Whether the read was successful.
        """
        try:
            with open(path, "r") as f:
                try:
                    tex_code = f.read()
                    return tex_code, True
                except UnicodeDecodeError:
                    return None, False
        except FileNotFoundError:
            return None, False

    def search_for_latex_files(self, src_dir: str, work_dir: str) -> List[str]:
        """Search for LaTeX files in the given directory and its subdirectories.

        Args:
            src_dir: The directory to search for LaTeX files.
            work_dir: The directory to save the assets to.

        Returns:
            List[str]: The list of LaTeX codes found in the directory.
        """
        list_tex_code: List[str] = []
        for root, _, files in os.walk(src_dir):
            for file in files:
                if file.endswith(".tex"):
                    # Read the Latex file
                    file_path: str = os.path.join(root, file)
                    latex_code, read_successful = LatexCompiler.read_latex_file(
                        file_path
                    )
                    if not read_successful:
                        continue

                    # Rename the assets
                    assert latex_code is not None
                    latex_code = self.rename_and_save_assets(
                        latex_code=latex_code,
                        src_path=src_dir,
                        dest_path=work_dir,
                    )
                    list_tex_code.append(latex_code)

        return list_tex_code

    def get_delimited_content(self, src_code: str) -> Dict[str, List[str]]:
        """Given a tex source code, return a dictionarry mapping categories (equation, plot, table, ...) to
        all the instances of that category in the source codes.

        Args:
            src_code (str): tex source code.

        Returns:
            Dict[str, List[str]]: Dictionnary mapping a category to the list of delimited instances
        """
        delimited_content: Dict[str, List[str]] = {}

        for category, (must_contain, delimiters) in TEX_DELIMITERS.items():
            # Skip the category if it is not in the list of categories
            if category not in self._categories:
                continue

            delimited_content[category] = []
            for delimiter in delimiters:
                start, end = delimiter
                lines = src_code.split("\n")  # Split the source code into lines
                start_idx, end_idx = None, None
                content = ""

                for line in lines:
                    stripped_line = line.strip()

                    # Skip commented lines
                    if stripped_line.startswith("%"):
                        continue

                    # Check for the start delimiter
                    if start_idx is None:
                        if start in stripped_line:
                            start_idx = lines.index(line)
                            content += line + "\n"
                            continue

                    # If we are in an environment, add the line to content
                    if start_idx is not None:
                        content += line + "\n"

                    # Check for the end delimiter
                    if end in stripped_line:
                        end_idx = lines.index(line)
                        if start_idx is not None and end_idx is not None:
                            # We only add the content to the category if it contains the must_contain string
                            if must_contain is None or must_contain in content:
                                delimited_content[category].append(content)
                            start_idx, end_idx = None, None
                            content = ""

            # Remove duplicates
            delimited_content[category] = list(set(delimited_content[category]))

        return delimited_content

    def get_and_save_rendering_from_delimited_content(
        self,
        delimited_content: Dict[str, List[str]],
        assets_path: str,
        dest_path: str,
    ) -> Dict[str, int]:
        """Given a dictionnary of delimited content, render all the images.
        Save them directly.

        Args:
            delimited_content (Dict[str, List[str]]): Dictionnary mapping a category to the list of delimited instances
            assets_path (str): Path to the assets
            dest_path (str): Path to the destination folder

        Returns:
            Dict[str, int]: Dictionnary mapping a category to the number of images rendered
        """

        num_done: Dict[str, int] = {}

        for category, list_of_content in delimited_content.items():
            os.makedirs(f"{dest_path}/images/{category}s", exist_ok=True)
            os.makedirs(f"{dest_path}/contents/{category}s", exist_ok=True)
            os.makedirs(f"{dest_path}/assets", exist_ok=True)

            num_images = 0
            offset = self._num_instances - self._num_to_do[category]
            num_max_image = self._num_to_do[category]

            for tex_code in list_of_content:
                try:
                    # Render the image
                    image, _ = LatexCompiler.latex_to_image(
                        TEX_BEGIN + tex_code + TEX_END,
                        assets_path=assets_path,
                        crop=True,
                    )

                    # Check if the image is not fully white
                    if image is None or np.allclose(image, 255):
                        continue

                    # Save the associated assets
                    asset_names = LatexCompiler.get_asset_names_used(tex_code)
                    for asset_name in asset_names:
                        asset_path = os.path.join(assets_path, asset_name)
                        new_asset_path = os.path.join(
                            f"{dest_path}/assets", asset_name.replace("/", "_")
                        )
                        try:
                            shutil.copy(asset_path, new_asset_path)
                        except FileNotFoundError:
                            # Could not copy one of the assets so ignore this tex_code
                            continue

                    # Save the image
                    image.save(
                        f"{dest_path}/images/{category}s/{category}_{num_images + offset}.png"
                    )

                    # Save the associated code
                    with open(
                        f"{dest_path}/contents/{category}s/{category}_{num_images + offset}.tex",
                        "w",
                    ) as f:
                        f.write(tex_code)

                    # Once we have enough images, stop rendering
                    num_images += 1
                    if num_images >= num_max_image:
                        break

                # There was an error rendering or saving the code, go to the next code
                except Exception:
                    continue

            num_done[category] = num_images

        return num_done

    def compile(self, data_path: str, destination_path: str) -> Dict[str, Any]:
        """
        Compile the given data into a webpage using Jekyll.

        Args:
            data_path: The path to the repository to compile.
            destination_path: The path to save the compiled data to.

        Returns:
            Dict[str, Any]: The information about the compilation.

        Raises:
            CompilationError: If the compilation fails.
        """

        infos: Dict[str, Any] = {}

        # 0. Create the directories
        src_dir: str = os.path.join(destination_path, "tmp/src")
        work_dir: str = os.path.join(destination_path, "tmp/work")
        os.makedirs(src_dir, exist_ok=True)
        os.makedirs(work_dir, exist_ok=True)

        # 1. Unzip the file
        try:
            with tarfile.open(data_path, "r:gz") as tar:
                # Extract all the contents into the current directory
                tar.extractall(path=src_dir)
        except tarfile.ReadError:
            raise CompilationError(f"Failed to extract the tar file: {data_path}")

        # 2. Search for the LaTeX files
        list_tex_code: List[str] = self.search_for_latex_files(src_dir, work_dir)

        # 3. Delimit the content
        categories = [
            category for category, value in self._num_to_do.items() if value > 0
        ]
        delimited_content: Dict[str, List[str]] = {
            category: [] for category in categories
        }
        for src_code in list_tex_code:
            tmp_delimited_content = self.get_delimited_content(src_code)
            for category in delimited_content.keys():
                delimited_content[category] += tmp_delimited_content[category]

        # 4. Shuffle the content
        for category in delimited_content.keys():
            random.shuffle(delimited_content[category])

        # 5. Render and save some code
        num_done: Dict[str, int] = self.get_and_save_rendering_from_delimited_content(
            delimited_content=delimited_content,
            assets_path=work_dir,
            dest_path=destination_path,
        )

        # 6. Save the information
        infos["num_done"] = num_done

        return infos
