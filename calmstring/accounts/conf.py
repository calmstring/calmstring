import sys
from django.conf import settings as dj_settings


class Conf:
    def _setting(self, name, default):
        conf = getattr(dj_settings, "CALMSTRING", {})
        return conf.get(name, default)

    @property
    def ACCOUNTS_CODE_EXPIRATION_TIME(self):
        return self._setting("ACCOUNTS_CODE_EXPIRATION_TIME", 600)


conf = Conf()

conf.__name__ = __name__
sys.modules[__name__] = conf
