import os
from pathlib import Path
import platform
import subprocess
from subprocess import CalledProcessError
import re

from future.utils import raise_from
from data import Data as I
from data.decorators import data
from tempdir import TempDir

# Adapted and simplified from latex package


class LatexMkBuilder(object):
    """A latexmk based builder for LaTeX files.

    Uses the `latexmk
    <http://users.phys.psu.edu/~collins/software/latexmk-jcc/>`_ script to
    build latex files, which is part of some popular LaTeX distributions like
    `texlive <https://www.tug.org/texlive/>`_.

    The build process consists of copying the source file to a temporary
    directory and running latexmk on it, which will take care of reruns.
    """

    def __init__(self):
        # The path to the ``xelatex`` binary (will be looked up on ``$PATH``).
        self.xelatex = 'xelatex'

    @data('source')
    def build_pdf(self, source, texinputs=[]):
        texinputs.append(bytes.decode(subprocess.check_output(['which', 'xelatex'])).strip())
        with TempDir() as tmpdir,\
                source.temp_saved(suffix='.latex', dir=tmpdir) as tmp:

            # close temp file, so other processes can access it also on Windows
            tmp.close()

            base_fn = os.path.splitext(tmp.name)[0]
            output_fn = base_fn + '.pdf'

            args = [self.xelatex,
                    tmp.name, ]

            # create environment
            newenv = os.environ.copy()
            newenv['TEXINPUTS'] = os.pathsep.join(texinputs) + os.pathsep

            try:
                subprocess.check_call(args,
                                      cwd=tmpdir,
                                      env=newenv,
                                      stdin=open(os.devnull, 'r'),
                                      stdout=open(os.devnull, 'w'),
                                      stderr=open(os.devnull, 'w'), )
            except CalledProcessError as e:
                raise_from(LatexBuildError(base_fn + '.log'), e)

            return I(open(output_fn, 'rb').read(), encoding=None)


class LatexBuildError(Exception):
    """LaTeX call exception."""

    # the binary log is probably latin1 or utf8?
    # utf8 throws errors occasionally, so we try with latin1
    # and

    def __init__(self, logfn=None):
        if os.path.exists(logfn):
            binlog = open(logfn, 'rb').read()
            self.log = binlog.decode(self.LATEX_MESSAGE_ENCODING, 'ignore')
        else:
            self.log = None

    def __str__(self):
        return str(self.log)

    def get_errors(self, *args, **kwargs):
        """Parse the log for errors.

        Any arguments are passed on to :func:`.parse_log`.

        :return: The return of :func:`.parse_log`, applied to the log
                 associated with this build error.
        """
        return self.parse_log(self.log)

    def parse_log(self, log, context_size=3):
        """Parses latex log output and tries to extract error messages.

        Requires ``-file-line-error`` to be active.

        :param log: The contents of the logfile as a string.
        :param context_size: Number of lines to keep as context, including the
                             original error line.
        :return: A dictionary containig ``line`` (line number, an int), ``error``,
                 (the error message), ``filename`` (name of the temporary file
                 used for building) and ``context`` (list of lines, starting with
                 with the error line).
        """
        lines = log.splitlines()
        errors = []

        for n, line in enumerate(lines):
            m = self.LATEX_ERR_RE.match(line)
            if m:
                err = m.groupdict().copy()
                err['context'] = lines[n:n + context_size]
                try:
                    err['line'] = int(err['line'])
                except TypeError:
                    pass  # ignore invalid int conversion
                errors.append(err)

        return errors
