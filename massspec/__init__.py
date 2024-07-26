# -*- coding: utf-8 -*-

# from .live_view import LiveView
from pathlib import Path
import inspect
import os

from . import utils
base_path = Path(os.sep.join(inspect.getfile(utils).split(os.sep)[:-1]))
MPL_STYLE_PATH = base_path / 'tavadze.mplstyle'
from matplotlib.pylab import style
style.use(MPL_STYLE_PATH)
from . import core
# from .core.raw_file import RawFile
# from .core.raw_file import RawFileCollection
# # from .core.run import LiveView
# # from .utils.export_to_excel import to_excel
# from .core.run import LiveView
