#  Copyright  2021 Alexis Lopez Zubieta
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
import re
import subprocess

from appimagebuilder.utils import shell


class FilePackageResolver:
    """Resolve which package provide a given file using `pacman -F`"""

    REQUIRED_COMMANDS = ["pacman"]

    def __init__(self):
        self.logger = logging.getLogger(str(self.__class__.__name__))
        self._cli_tools = shell.require_executables(self.REQUIRED_COMMANDS)

    def resolve(self, files) -> {}:
        output = self._run_pacman_f(files)
        results = self._parse_pacman_f_output(output)
        return results

    def _run_pacman_f(self, files):

        argumentCharacters = len(" ".join(files))+20 # 20 lenght of string "/usr/bin/pacman -Qo "
        print(argumentCharacters)
        split = False
        if argumentCharacters >= 65537:
            split = True

        # make sure that the files are str
        files = [str(file) for file in files]

        # ensure C locale is used to avoid locales affecting the output format
        env = os.environ.copy()
        env["LC_ALL"] = "C"

        if split == False:
            command = "{pacman} -Qo {files}"
            command = command.format(**self._cli_tools, files=" ".join(files))
            self.logger.info(command)
            _proc = subprocess.run(command, stdout=subprocess.PIPE, shell=True, env=env)
            stdout_data = _proc.stdout.decode()
            return stdout_data
        else:
            # Calculate number of files then divide in half
            TotalNumberOfFiles = len(files)
            print(TotalNumberOfFiles)
            if TotalNumberOfFiles%2 == 0:
                totalNumberOfHalfFiles = int (TotalNumberOfFiles/2)
            else:
                totalNumberOfHalfFiles = int ((TotalNumberOfFiles-1)/2)
            halfFiles1 = files[1:totalNumberOfHalfFiles]
            halfFiles2 = files[totalNumberOfHalfFiles:TotalNumberOfFiles]
            command1="{pacman} -Qo {halfFiles1}"
            command2="{pacman} -Qo {halfFiles2}"

            print(halfFiles2)
            command1 = command1.format(**self._cli_tools, halfFiles1=" ".join(halfFiles1))
            command2 = command2.format(**self._cli_tools, halfFiles2=" ".join(halfFiles2))
            self.logger.info(command1)
            _proc1 = subprocess.run(command1, stdout=subprocess.PIPE, shell=True, env=env)
            self.logger.info(command2)
            _proc2 = subprocess.run(command2, stdout=subprocess.PIPE, shell=True, env=env)
            stdout_data1 = _proc1.stdout.decode()
            stdout_data2 = _proc2.stdout.decode()
            return stdout_data1


    @staticmethod
    def _parse_pacman_f_output(output):
        results = {}
        for match in re.findall(
            r"(?P<file>.*) is owned by (?P<pkg_name>.*) (?P<pkg_version>.*)", output
        ):
            file = pathlib.Path(match[0])
            pkg_name = match[1]
            pkg_name = pkg_name.split("/")[-1]
            results[file] = pkg_name
        return results
