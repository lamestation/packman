# -*- coding: utf-8 -*-
import os, re, sys
import plistlib
import subprocess
import shutil
import glob
import time

import packthing.util as util

REQUIRE = [ 'macdeployqt' ]

KEYS = [ 'category', 'background', 'bundle' ]

from . import _base

class Packager(_base.Packager):

    def __init__(self, config, files):
        super(Packager,self).__init__(config, files)

        self.volumename = self.packagename()

        self.EXT = 'dmg'
        self.EXT_BIN = ''
        self.EXT_LIB = 'dylib'
        self.DIR_PACKAGE = os.path.join(self.DIR_STAGING,'mac')
        self.DIR_BUNDLE = os.path.join(self.DIR_PACKAGE,self.config['name']+'.app')
        self.DIR_OUT = os.path.join(self.DIR_BUNDLE,'Contents')

        self.OUT['bin'] = 'MacOS'
        self.OUT['lib'] = 'MacOS'
        self.OUT['share'] = 'Resources'

    def get_path(self):
        return self.DIR_BUNDLE

    def bundle_identifier(self):
        return 'com.'+self.config['org'].lower()+self.config['name']

    def build_plist(self, config, target):
        pl = dict(
            CFBundleDevelopmentRegion = "English",
            CFBundleDisplayName = self.config['name'],
            CFBundleExecutable = self.config['package'],
            CFBundleIconFile = "mac.icns",
            CFBundleIdentifier = self.bundle_identifier(),
            CFBundleInfoDictionaryVersion = "6.0",
            CFBundleName = self.config['name'],
            CFBundlePackageType = "APPL",
            CFBundleShortVersionString = self.config['version'],
            CFBundleVersion = "1",
            LSApplicationCategoryType = self.config['category'],
            LSMinimumSystemVersion = "10.7",
            NSHumanReadableCopyright = u"Copyright © "
                    + str(self.config['copyright'])
                    + ", "+self.config['org']+". "
                    + self.config['name']
                    + " is released under the "
                    + self.config['license']+" license.",
            NSPrincipalClass = "NSApplication",
            NSSupportsSuddenTermination = "YES",
        )
        return pl

    def mac_installer(self):
        d = {
            'VOLUME'    : self.volumename,
            'BACKGROUND': os.path.basename(self.config['background']),
            'BUNDLE'    :os.path.basename(self.DIR_BUNDLE),
        }
        return util.get_template('dmg/installer.AppleScript').substitute(d)

    def mac_install(self):
        d = {
            'VOLUME'    : self.volumename,
        }
        return util.get_template('dmg/install.AppleScript').substitute(d)

    def make(self):
        super(Packager,self).make()
        with util.pushd(self.DIR_OUT):
            plistlib.writePlist(self.build_plist(self.config, None), 
                    os.path.join(self.DIR_OUT,'Info.plist'))

    def generate_icon(self,icon,size,targetdir,addition=False):
        iconname = 'icon_'
        if addition == True:
            iconname += str(int(size)/2)+'x'+str(int(size)/2)
            iconname += '@2x'
        else:
            iconname += size+'x'+size
        iconname += '.png'
        util.command(['sips','-z',size,size,icon,
                '--out',os.path.join(targetdir,iconname)])

    def icon(self,icon,target):
        if os.path.exists(icon):
            if target == self.config['bundle']:
                DIR_ICNS = os.path.join(self.DIR_STAGING,'mac.iconset')
                util.mkdir(DIR_ICNS)
                self.generate_icon(icon,'16',DIR_ICNS,False)
                self.generate_icon(icon,'32',DIR_ICNS,True)
                self.generate_icon(icon,'32',DIR_ICNS,False)
                self.generate_icon(icon,'64',DIR_ICNS,True)
                self.generate_icon(icon,'64',DIR_ICNS,False)
                self.generate_icon(icon,'128',DIR_ICNS,False)
                self.generate_icon(icon,'256',DIR_ICNS,True)
                self.generate_icon(icon,'256',DIR_ICNS,False)
                self.generate_icon(icon,'512',DIR_ICNS,True)
                self.generate_icon(icon,'512',DIR_ICNS,False)
                util.command(['iconutil','-c','icns',
                    '--output',os.path.join(self.DIR_OUT,self.OUT['share'],'mac.icns'),DIR_ICNS])
                shutil.rmtree(DIR_ICNS)
        else:
            util.error("Icon does not exist:", icon)

    def finish(self):
        super(Packager,self).finish()

        size = util.command(['du','-s',self.DIR_BUNDLE])[0].split()[0]
        size = str(int(size)+1000)
        tmpdevice = os.path.join(self.DIR_PACKAGE, 'pack.temp.dmg')

        existingdevices = glob.glob("/Volumes/"+self.volumename+"*")
        for d in existingdevices:
            try:
                util.command(['hdiutil','detach',d])
            except subprocess.CalledProcessError as e:
                util.error("Couldn't unmount "+d+"; close all programs using this Volume and try again.")

        util.command(['hdiutil','create',
            '-format','UDRW',
            '-srcfolder',self.DIR_BUNDLE,
            '-volname',self.volumename,
            '-size',size+'k',
            tmpdevice])

        util.command(['hdiutil','attach',
            '-readwrite',
            tmpdevice])

        time.sleep(5)
        util.command(['sync'])

        self.volume = "/Volumes/"+self.volumename

        DIR_VOLUME = os.path.join(os.sep,'Volumes',self.volumename,'.background')
        util.copy(self.config['master']+"/"+self.config['background'], DIR_VOLUME)

        print self.mac_installer()
        util.command(['osascript'], stdinput=self.mac_installer())

        util.command(['chmod','-Rf','go-w',DIR_VOLUME])
        util.command(['chmod','-Rf','go-w',
                        os.path.join(os.path.dirname(DIR_VOLUME),
                        self.config['name']+'.app')])
        util.command(['chmod','-Rf','go-w',
                        os.path.join(os.path.dirname(DIR_VOLUME),
                        'Applications')])

        util.command(['sync'])
        util.command(['hdiutil','detach',self.volume])
        util.command(['hdiutil','convert',
                tmpdevice,
                '-format','UDZO',
                '-imagekey',
                'zlib-level=9',
                '-o',os.path.join(self.DIR_STAGING, self.packagename()+'.dmg')])

        util.command(['sync'])

        os.remove(tmpdevice)

    def install(self):
        with util.pushd(self.DIR_STAGING):
            try:
                util.command(['hdiutil','attach',
                    '-readonly',
                    os.path.join(self.DIR_STAGING, self.packagename()+'.dmg')])
                util.command(['sync'])
                util.command(['osascript'], stdinput=self.mac_install())
            except:
                util.error("Installation failed! Oh, well.")
