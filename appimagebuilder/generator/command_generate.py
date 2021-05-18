#  Copyright 2020 Anupam Basak <anupam.basak27@gmail.com>
#
#  Permission is hereby granted, free of charge, to any person obtaining a
#  copy of this software and associated documentation files (the "Software"),
#  to deal in the Software without restriction, including without limitation the
#  rights to use, copy, modify, merge, publish, distribute, sublicense, and/or
#  sell copies of the Software, and to permit persons to whom the Software is
#  furnished to do so, subject to the following conditions:
#
#  The above copyright notice and this permission notice shall be included in
#  all copies or substantial portions of the Software.

import logging
import os
import pathlib
import shutil

from ruamel.yaml import YAML

from appimagebuilder.generator.app_runtime_analyser import AppRuntimeAnalyser
from appimagebuilder.generator.bundle_info_gatherer import BundleInfoGatherer
from appimagebuilder.generator.bundle_info_gatherer_cli import BundleInfoGathererCLI
from appimagebuilder.generator.desktop_entry_parser import DesktopEntryParser
from appimagebuilder.generator.package_managers.apt import (
    FilePackageResolver,
    PackageRepositoryResolver,
)
from appimagebuilder.generator.recipe_generator import RecipeGenerator
from appimagebuilder.generator.recipe_sections.apt_section_generator import (
    AptSectionGenerator,
)
from appimagebuilder.generator.recipe_sections.files_section_generator import (
    FilesSectionGenerator,
)


class GenerateMethodError(RuntimeError):
    pass


class CommandGenerate:
    def __init__(self):
        self.logger = logging.getLogger("Generator")

        self.logger.info("Searching AppDir")
        self.app_dir = self._locate_app_dir()

        # configure Recipe Generator
        package_manager_section_generators = []
        if shutil.which("apt-get"):
            file_package_resolver = FilePackageResolver()
            package_repository_resolver = PackageRepositoryResolver()
            apt_section_generator = AptSectionGenerator(
                file_package_resolver, package_repository_resolver
            )
            package_manager_section_generators.append(apt_section_generator)

        # append files section generator at last as it will catch all the dependencies
        package_manager_section_generators.append(FilesSectionGenerator())

        bundle_info_gatherer_ui = BundleInfoGathererCLI()
        desktop_entry_parser = DesktopEntryParser()
        bundle_info_gatherer = BundleInfoGatherer(
            bundle_info_gatherer_ui, desktop_entry_parser
        )

        runtime_analyser = AppRuntimeAnalyser()
        self.generator = RecipeGenerator(
            package_manager_section_generators, bundle_info_gatherer, runtime_analyser
        )

    def generate(self):
        recipe = self.generator.generate(self.app_dir)
        self._write_recipe_file(recipe)

        self.logger.info("Recipe generation completed.")

    def _write_recipe_file(self, recipe):
        yaml = YAML()
        yaml.default_flow_style = False

        recipe_header = "# appimage-builder recipe see https://appimage-builder.readthedocs.io for details\n"
        with open("AppImageBuilder.yml", "w") as f:
            f.write(recipe_header)
            yaml.dump(recipe, f)

    @staticmethod
    def _locate_app_dir():
        for file_name in os.listdir(os.path.curdir):
            if os.path.isdir(file_name) and file_name.lower() == "appdir":
                return pathlib.Path(file_name).absolute()

        raise GenerateMethodError(
            "Unable to find an AppDir, this is required to create a recipe."
        )
