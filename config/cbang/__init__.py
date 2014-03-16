from SCons.Script import *
import inspect
import os


def GetHome():
    path = inspect.getfile(inspect.currentframe())
    return os.path.dirname(os.path.abspath(path))


def ConfigLocalBoost(env):
    boost_source = os.environ.get('BOOST_SOURCE', None)
    if not boost_source: raise Exception, 'BOOST_SOURCE not set'

    env.Append(CPPPATH = [boost_source])
    env.PrependUnique(LIBPATH = [GetHome() + '../../lib'])

    if env.get('compiler') == 'gnu':
        env.Append(CCFLAGS = '-Wno-unused-local-typedefs')

    return boost_source


def ConfigBoost(conf, require = False):
    return conf.CBConfig('boost', require, version = '1.40',
                         hdrs = ['version', 'iostreams/stream', 'ref',
                                 'spirit/version',
                                 'interprocess/sync/file_lock',
                                 'date_time/posix_time/posix_time'],
                         libs = ['iostreams', 'system', 'filesystem', 'regex'])


def configure_deps(conf, local = True):
    env = conf.env

    conf.CBConfig('zlib', not local)
    conf.CBConfig('bzip2', not local)
    conf.CBConfig('XML', not local)
    conf.CBConfig('sqlite3', not local)

    if not ConfigBoost(conf) and not local:
        env.ConfigLocalBoost()
        ConfigBoost(conf, True)

    conf.CBConfig('openssl', version = '1.0.0')
    conf.CBConfig('v8', False)

    if env['PLATFORM'] == 'win32':
        conf.CBRequireLib('wsock32')
        conf.CBRequireLib('setupapi')

    else: conf.CBConfig('pthreads')

    # OSX frameworks
    if env['PLATFORM'] == 'darwin':
        conf.CBConfig('osx')
        if not (conf.CheckOSXFramework('CoreServices') and
                conf.CheckOSXFramework('IOKit') and
                conf.CheckOSXFramework('CoreFoundation')):
            raise Exception, \
                'Need CoreServices, IOKit & CoreFoundation frameworks'

    conf.CBConfig('valgrind', False)

    # Debug
    if env.get('debug', 0):
        if conf.CBCheckCHeader('execinfo.h') and \
                conf.CBCheckCHeader('bfd.h') and \
                conf.CBCheckLib('iberty') and conf.CBCheckLib('bfd'):
            env.CBDefine('HAVE_CBANG_BACKTRACE')

        elif env.get('backtrace_debugger', 0):
            raise Exception, \
                'execinfo.h, bfd.h and libbfd needed for backtrace_debuger'

        env.CBDefine('DEBUG_LEVEL=' + str(env.get('debug_level', 1)))


def configure(conf):
    env = conf.env

    home = GetHome() + '/../..'
    env.AppendUnique(CPPPATH = [home + '/src', home + '/include'])
    env.AppendUnique(LIBPATH = [home + '/lib'])

    if not env.CBConfigEnabled('cbang-deps'):
        conf.CBConfig('cbang-deps', local = False)

    conf.CBRequireLib('cbang')
    conf.CBRequireCXXHeader('cbang/Exception.h')
    env.CBDefine('HAVE_CBANG')


def generate(env):
    env.CBAddConfigTest('cbang', configure)
    env.CBAddConfigTest('cbang-deps', configure_deps)
    env.AddMethod(ConfigLocalBoost)

    env.CBAddVariables(
        BoolVariable('backtrace_debugger', 'Enable backtrace debugger', 0),
        ('debug_level', 'Set log debug level', 1))

    env.CBLoadTools(
        'sqlite3 boost openssl pthreads valgrind osx zlib bzip2 XML v8'.split(),
        GetHome() + '/..')


def exists(env):
    return 1
