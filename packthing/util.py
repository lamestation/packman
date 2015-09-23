from __future__ import print_function
import os, sys
import subprocess
from contextlib import contextmanager
import string
import errno
import tarfile

def warning(*objs):
    print("WARNING:", *objs, file=sys.stderr)

def error(*objs):
    blocks = []
    for b in ' '.join(objs).split('\n'):
        if len(blocks) > 0:
            blocks.append("       "+b)
        else:
            blocks.append(b)

    print("\nERROR:", "\n".join(blocks), file=sys.stderr)
    print()
    sys.exit(1)

def subtitle(text):
    line = (80-(len(text)+2))/2
    print("-"*line,text,"-"*(line+(len(text) % 2)))

def title(text):
    line = (80-(len(text)+2))/2
    print("="*line,text.upper(),"="*(line+(len(text) % 2)))

def headline(func):
    def wrapper(*args, **kwargs):
        title(func.__name__)
        res = func(*args, **kwargs)
        return res
    return wrapper

@contextmanager
def pushd(newDir):
    previousDir = os.getcwd()
    os.chdir(newDir)
    yield
    os.chdir(previousDir)

def command(args,verbose=True, strict=True, stdinput=None):
    if verbose:
        print("-",' '.join(args))
    try:
        process = subprocess.Popen(args, stdout=subprocess.PIPE,
                stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    except OSError as e:
        error("Command '"+args[0]+"' not found; exiting.")

    out, err = process.communicate(input=stdinput)
    if strict:
        if process.returncode:
            print(err)
            raise subprocess.CalledProcessError(process.returncode, args, err)
    return out, err

def command_in_dir(args, newdir, verbose=True, strict=True, stdinput=None):
    with pushd(newdir):
        out, err = command(args,verbose=verbose, strict=strict)
        return out, err

def table(path, version, url):
    return "%30s  %10s  %s" % (path, version, url)

def which(program):
    def is_exe(fpath):
        return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

    fpath, fname = os.path.split(program)
    if fpath:
        if is_exe(program):
            return program
    else:
        for path in os.environ["PATH"].split(os.pathsep):
            path = path.strip('"')
            exe_file = os.path.join(path, program)
            if is_exe(exe_file):
                return exe_file

    return None

def mkdir(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def archive(name, files):
    shortname = os.path.basename(name)

    tar = tarfile.open(name=name, mode='w:gz')
    for f in files:
        tar.add(name=f, arcname=os.path.join(os.path.splitext(shortname)[0],f), recursive=False)
    tar.close()

def from_scriptroot(filename):
    currentpath = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(currentpath,filename)

def get_template(template, substitute=dict()):
    template = os.path.join('template',template)
    template = from_scriptroot(template)
    return string.Template(open(template,'r').read())



#python-chroot-builder
#Copyright (C) 2012 Ji-hoon Kim
#
#This program is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 3 of the License, or
#(at your option) any later version.
#
#This program is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#
#You should have received a copy of the GNU General Public License
#along with this program.  If not, see <http://www.gnu.org/licenses/>.
#-----------------------------------------
def ldd(filenames):
    libs = [] 
    for x in filenames:
        p = subprocess.Popen(['ldd', x], 
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE)

        result = p.stdout.readlines()

        for x in result:
            s = x.split()
            s.pop(1)
            s.pop()
            if len(s) == 2:
                libs.append(s)
	return libs
#-----------------------------------------

def extract_libs(files, libs):
    resultlibs = []
    for f in files:
        for l in ldd([which(f)]):
            for lib in libs:
                if l[0].find(lib) == -1:
                    pass
                else:
                    resultlibs.append(l)
    return sorted(list(set(tuple(lib) for lib in resultlibs)))

def write(text, filename):
    f = open(filename, 'w')
    f.seek(0)
    f.write(text)
    f.close()

def create(text, filename):
    print("Create",filename)
    mkdir(os.path.dirname(filename))
    f = open(filename, 'w')
    f.seek(0)
    f.write(text)
    f.close()
    os.chmod(filename, 0644)
