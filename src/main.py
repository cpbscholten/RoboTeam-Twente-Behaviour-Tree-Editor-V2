from model.editor_settings import *


logging.basicConfig(level=logging.ERROR,
                    format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                    datefmt='%m-%d %H:%M',
                    filename=query_setting("logfile_name", "main"),
                    filemode='w')
