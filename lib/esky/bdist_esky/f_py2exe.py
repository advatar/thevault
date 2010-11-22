#  Copyright (c) 2009-2010, Cloud Matrix Pty. Ltd.
#  All rights reserved; available under the terms of the BSD License.
"""

  esky.bdist_esky.f_py2exe:  bdist_esky support for py2exe

"""

from __future__ import with_statement


import os
import re
import sys
import imp
import time
import zipfile
import marshal
import struct
import shutil
import inspect
import zipfile
import ctypes
from glob import glob


from py2exe.build_exe import py2exe

import esky
from esky.util import is_core_dependency, ESKY_CONTROL_DIR
from esky import winres

try:
    import py2exe.mf as modulefinder
except ImportError:
    modulefinder = None

#  Hack to make win32com work seamlessly with py2exe
if modulefinder is not None:
  try:
    import win32com
    for p in win32com.__path__[1:]:
        modulefinder.AddPackagePath("win32com", p)
    for extra in ["win32com.shell"]: #,"win32com.mapi"
        __import__(extra)
        m = sys.modules[extra]
        for p in m.__path__[1:]:
           modulefinder.AddPackagePath(extra, p)
  except ImportError:
     pass


class custom_py2exe(py2exe): 
    """Custom py2exe command subclass.

    This py2exe command subclass incorporates some well-known py2exe "hacks"
    to make common third-party packages work better.
    """

    def create_modulefinder(self):
        mf = py2exe.create_modulefinder(self)
        self.__mf = mf
        return mf

    def build_manifest(self,target,template):
        (mfest,mid) = py2exe.build_manifest(self,target,template)
        #  Hack to get proper UI theme when freezing wxPython
        if mfest is not None:
            if "wx" in self.__mf.modules:
                mfest = mfest.replace("</assembly>","""
                    <dependency>
                      <dependentAssembly>
                        <assemblyIdentity
                         type="win32"
                         name="Microsoft.Windows.Common-Controls"
                         version="6.0.0.0"
                         processorArchitecture="*"
                         publicKeyToken="6595b64144ccf1df"
                         language="*" />
                      </dependentAssembly>
                   </dependency>
                 </assembly>""")
        return (mfest,mid)


def freeze(dist):
    """Freeze the given distribution data using py2exe."""
    includes = dist.includes
    excludes = dist.excludes
    options = dist.freezer_options
    #  Merge in any encludes/excludes given in freezer_options
    includes.append("esky")
    for inc in options.pop("includes",()):
        includes.append(inc)
    for exc in options.pop("excludes",()):
        excludes.append(exc)
    #  py2exe expects some arguments on the main distribution object.
    #  We handle data_files ourselves, so fake it out for py2exe.
    dist.distribution.console = []
    dist.distribution.windows = []
    my_data_files = dist.distribution.data_files
    dist.distribution.data_files = []
    for exe in dist.get_executables():
        #  Pass any executable kwds through to py2exe.
        #  We handle "icon" and "gui_only" ourselves.
        s = exe._kwds.copy()
        s["script"] = exe.script
        s["dest_base"] = exe.name[:-4]
        if exe.icon is not None and "icon_resources" not in s:
            s["icon_resources"] = [(1,exe.icon)]
        if exe.gui_only:
            dist.distribution.windows.append(s)
        else:
            dist.distribution.console.append(s)
    if "zipfile" in options:
        dist.distribution.zipfile = options.pop("zipfile")
    #  Create the py2exe cmd and adjust its options
    cmd = custom_py2exe(dist.distribution)
    cmd.includes = includes
    cmd.excludes = excludes
    for (nm,val) in options.iteritems():
        setattr(cmd,nm,val)
    cmd.dist_dir = dist.freeze_dir
    cmd.finalize_options()
    #  Actually run the freeze process
    cmd.run()
    #  Copy data files into the freeze dir
    dist.distribution.data_files = my_data_files
    for (src,dst) in dist.get_data_files():
        dst = os.path.join(dist.freeze_dir,dst)
        dstdir = os.path.dirname(dst)
        if not os.path.isdir(dstdir):
            dist.mkpath(dstdir)
        dist.copy_file(src,dst)
    #  Place a marker fileso we know how it was frozen
    os.mkdir(os.path.join(dist.freeze_dir,ESKY_CONTROL_DIR))
    marker_file = os.path.join(ESKY_CONTROL_DIR,"f-py2exe-%d%d.txt")%sys.version_info[:2]
    open(os.path.join(dist.freeze_dir,marker_file),"w").close()
    #  Copy package data into the library.zip
    #  For now, we don't try to put package data into a bundled zipfile.
    if dist.distribution.zipfile is not None:
        lib = zipfile.ZipFile(os.path.join(dist.freeze_dir,"library.zip"),"a")
        for (src,arcnm) in dist.get_package_data():
            lib.write(src,arcnm)
        lib.close()
    else:
        for (src,arcnm) in dist.get_package_data():
            err = "zipfile=None can't be used with package_data (yet...)"
            raise RuntimeError(err)
    #  There's no need to copy library.zip into the bootstrap env, as the
    #  chainloader will run before py2exe goes looking for it.
    pass
    #  Create the bootstraping code, using custom code if specified.
    #  It gets stored as a marshalled list of code objects directly in the exe.
    code_source = [inspect.getsource(esky.bootstrap)]
    code_source.append(_FAKE_ESKY_BOOTSTRAP_MODULE)
    code_source.append(_CUSTOM_WIN32_CHAINLOADER)
    code_source.append("__esky_name__ = '%s'" % (dist.distribution.get_name(),))
    code_source.append(dist.get_bootstrap_code())
    code_source.append("bootstrap()")
    code_source = "\n".join(code_source)
    code = marshal.dumps([compile(code_source,"__main__.py","exec")])
    coderes = struct.pack("iiii",
                     0x78563412, # a magic value used for integrity checking,
                     0, # no optimization
                     False,  # normal buffered output
                     len(code),
                     ) + "\x00" + code + "\x00\x00"
    #  We try to bundle the python DLL into all bootstrap executables, even
    #  if it's not bundled in the frozen distribution.  This helps keep the
    #  bootstrap env small and minimises the chances of something going wrong.
    pydll = u"python%d%d.dll" % sys.version_info[:2]
    frozen_pydll = os.path.join(dist.freeze_dir,pydll)
    if os.path.exists(frozen_pydll):
        for nm in os.listdir(dist.freeze_dir):
            if nm == pydll:
                continue
            if nm.lower().endswith(".pyd") or nm.lower().endswith(".dll"):
                #  There's an unbundled C-extension, so we can't bundle
                #  the DLL or our bootstrapper won't work.
                pydll_bytes = None
                break
        else:
            with open(frozen_pydll,"rb") as f:
                pydll_bytes = f.read()
    else:
        #  They've bundlded the dll into the zipfile.  Rather than parse
        #  it back out, I'm just going to grab it from the filesystem.
        sz = 0
        res = 0
        while res == sz:
            sz += 512
            buf = ctypes.create_string_buffer(sz)
            res = ctypes.windll.kernel32.GetModuleFileNameA(sys.dllhandle,ctypes.byref(buf),sz)
            if not res:
                raise ctypes.WinError()
        with open(buf.value,"rb") as f:
            pydll_bytes = f.read()
    #  Copy any core dependencies into the bootstrap env.
    for nm in os.listdir(dist.freeze_dir):
        if is_core_dependency(nm):
            if nm == pydll and pydll_bytes is not None:
                continue
            dist.copy_to_bootstrap_env(nm)
    #  Copy the loader program for each script into the bootstrap env.
    for exe in dist.get_executables(normalise=False):
        if not exe.include_in_bootstrap_env:
            continue
        exepath = dist.copy_to_bootstrap_env(exe.name)
        #  Insert the bootstrap code into the exe as a resource.
        #  This appears to have the happy side-effect of stripping any extra
        #  data from the end of the exe, which is exactly what we want when
        #  zipfile=None is specified; otherwise each bootstrap EXE would also
        #  contain the whole bundled zipfile.
        winres.add_resource(exepath,coderes,u"PYTHONSCRIPT",1,0)
        #  Inline the pythonXY.dll as a resource in the exe.
        if pydll_bytes is not None:
            winres.add_resource(exepath,pydll_bytes,pydll.upper(),1,0)

#  Code to fake out any bootstrappers that try to import from esky.
_FAKE_ESKY_BOOTSTRAP_MODULE = """
class __fake:
  __all__ = ()
sys.modules["esky"] = __fake()
sys.modules["esky.bootstrap"] = __fake()
"""


#  On Windows, execv is flaky and expensive.  If the chainloader is the same
#  python version as the target exe, we can munge sys.path to bootstrap it
#  into the existing process.
#
#  We need to read the script to execute as a resource from the exe, so this
#  only works if we can bootstrap a working ctypes module.  We then insert
#  the source code from esky.winres.load_resource directly into this function.
#
_CUSTOM_WIN32_CHAINLOADER = """
_orig_chainload = _chainload
def _chainload(target_dir):
  # careful to escape percent-sign, this gets interpolated below
  marker_file = pathjoin(ESKY_CONTROL_DIR,"f-py2exe-%%d%%d.txt")%%sys.version_info[:2]
  pydll = "python%%s%%s.dll" %% sys.version_info[:2]
  mydir = dirname(sys.executable)
  if not exists(pathjoin(target_dir,marker_file)):
      _orig_chainload(target_dir)
  else:
      for nm in listdir(target_dir):
          if nm == pydll:
              continue
          if nm.lower().startswith("msvcr"):
              continue
          if nm.lower().endswith(".pyd") or nm.lower().endswith(".dll"):
              #  The freeze dir contains unbundled C extensions.
              #  Since they're linked against a physical python DLL, we
              #  can't chainload them unless we have one too.
              if not exists(pathjoin(mydir,pydll)):
                  _orig_chainload(target_dir)
              else:
                  break
      sys.bootstrap_executable = sys.executable
      sys.executable = pathjoin(target_dir,basename(sys.executable))
      sys.argv[0] = sys.executable
      for i in xrange(len(sys.path)):
          sys.path[i] = sys.path[i].replace(mydir,target_dir)
      libfile = pathjoin(target_dir,"library.zip")
      if exists(libfile) and libfile not in sys.path:
          sys.path.append(libfile)
      try:
          import zipextimporter; zipextimporter.install()
      except ImportError:
          pass
      try:
          import nt
          import ctypes
          import struct
          import marshal
          import msvcrt
      except ImportError:
          _orig_chainload(target_dir)
      # the source for esky.winres.load_resource gets inserted below:
      from ctypes import c_char, POINTER
      k32 = ctypes.windll.kernel32
      LOAD_LIBRARY_AS_DATAFILE = 0x00000002
      _DEFAULT_RESLANG = 1033
      %s
      # now we magically have the load_resource function :-)
      try:
          data = load_resource(sys.executable,u"PYTHONSCRIPT",1,0)
      except EnvironmentError:
          #  This will trigger if sys.executable doesn't exist.
          #  Falling back to the original chainloader will account for
          #  the unlikely case where sys.executable is a backup file.
          _orig_chainload(target_dir)
      else:
          del sys.modules["esky"]
          del sys.modules["esky.bootstrap"]
          headsz = struct.calcsize("iiii")
          (magic,optmz,unbfrd,codesz) = struct.unpack("iiii",data[:headsz])
          assert magic == 0x78563412
          # Set up the environment requested by "optimized" and "unbuffered"
          try:
              opt_var = ctypes.c_int.in_dll(ctypes.pythonapi,"Py_OptimizeFlag")
              opt_var.value = optmz
          except ValueError:
              pass
          if unbfrd:
              msvcrt.setmode(0,nt.O_BINARY)
              msvcrt.setmode(1,nt.O_BINARY)
              ctypes.pythonapi.PyFile_AsFile.argtypes = (ctypes.py_object,)
              if hasattr(ctypes.cdll.msvcrt,"setvbuf"):
                  def setunbuf(f):
                      fp = ctypes.pythonapi.PyFile_AsFile(f)
                      ctypes.cdll.msvcrt.setvbuf(fp,None,4,512)
              else:
                  def setunbuf(fd,mode):
                      fp = ctypes.pythonapi.PyFile_AsFile(f)
                      ctypes.cdll.msvcrt.setbuf(fp,None)
              setunbuf(sys.stdin)
              setunbuf(sys.stdout)
              setunbuf(sys.stderr)
          # skip over the archive name to find start of code
          codestart = headsz
          while data[codestart] != "\\0":
              codestart += 1
          codestart += 1
          codelist = marshal.loads(data[codestart:codestart+codesz])
          # Execute all code in the context of __main__ module.
          # Remove our own cruft from it before doing so.
          d_locals = d_globals = sys.modules["__main__"].__dict__
          d_locals.clear()
          d_locals["__name__"] = "__main__"
          for code in codelist:
              exec code in d_globals, d_locals
          raise SystemExit(0)
""" % (inspect.getsource(winres.load_resource).replace("\n","\n"+" "*6),)


