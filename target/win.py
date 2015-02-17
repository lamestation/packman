import os
import util
import uuid, subprocess

from . import base

REQUIRE = [ 'iscc',
            'windeployqt',
            ]

class Packager(base.Packager):

    def __init__(self, info, version, files):
        super(Packager,self).__init__(info, version, files)

        self.EXT = 'exe'
        self.DIR_OUT = os.path.join(self.DIR_STAGING,'tmp')

        self.OUT['bin'] = ''
        self.OUT['lib'] = ''
        self.OUT['share'] = ''

    # Taken from innosetup module (https://pypi.python.org/pypi/innosetup/0.6.6)
    def AppID(self):
        src = self.info.attrib['url']
        appid = uuid.uuid5(uuid.NAMESPACE_URL, src).urn.rsplit(':', 1)[1]
        return '{{%s}' % appid

    def iss(self):
        script = util.get_template(os.path.join('win','installer.iss'))
        rendering = script.substitute(
                    APPID           = self.AppID(),
                    ORGANIZATION    = self.info.attrib['organization'],
                    NAME            = self.info.attrib['application'],
                    PACKAGENAME     = self.packagename(),
                    WEBSITE         = self.info.attrib['url'],
                    VERSION         = self.VERSION,
                    GRAPHICSPATH    = 'gfx',
                    OUTDIR          = self.DIR_OUT,
                    SHORTNAME       = self.NAME,
                )
        return rendering

    def make(self):
        super(Packager,self).make()
        with util.pushd(self.DIR_OUT):
            for f in self.files['bin']:
                util.command(['windeployqt',f])
            util.command(['iscc','-'],stdinput=self.iss())
