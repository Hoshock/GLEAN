# coding:UTF-8

import os
from collections import OrderedDict
from subprocess import check_output, STDOUT, CalledProcessError
try:
    import readline
except ImportError:
    print 'Warning: Tab completion and storing input histories will not work.'
else:
    import rlcompleter
    import glob

    def complete(text, state):
        line = readline.get_line_buffer().split()
        return [x for x in glob.glob(text+'*')][state]

    readline.set_completer_delims(' ')
    readline.parse_and_bind('tab: complete')
    readline.set_completer(complete)


class End(Exception):
    pass


class Interpreter(object):
    GREEN_COLOR  = '\033[92m'
    YELLOW_COLOR = '\033[93m'
    RED_COLOR    = '\033[91m'
    CLEAR_COLOR  = '\033[0m'
    NAME         = GREEN_COLOR + 'GLEAN' + CLEAR_COLOR
    VERSION      = YELLOW_COLOR + '0.91 (beta)' + CLEAR_COLOR
    CREATOR      = 'Tsuyoshi ISHIDA'
    CONTACT      = YELLOW_COLOR + 'tishida __at__ ioa.s.u-tokyo.ac.jp' + CLEAR_COLOR
    SYMBOL       = NAME + GREEN_COLOR + ' <{}>: ' + CLEAR_COLOR

    IMG_OPTION    = '-i'
    SRC_OPTION    = '-s'
    IMGSRC_OPTION = '-is'
    MDL_OPTION    = '-m'
    ERROR_CODE    = -1

    def __init__(self, glafic_i, glafic_s, glean):
        self.glafic_i  = glafic_i
        self.glafic_s  = glafic_s
        self.glean     = glean
        self.functions = {'go'      : self.go,       'gogo'    : self.gogo,     'quit'  : self.quit,   'exit'  : self.quit,
                          'get'     : self.get,      'set'     : self.set,      'reset' : self.reset,  'append': self.append,
                          'clear'   : self.clear,    'pwd'     : self.pwd,      'cd'    : self.cd,     'ls'    : self.ls,
                          'open'    : self.open,     'less'    : self.less,     'more'  : self.more,   'rm'    : self.rm,
                          'read'    : self.read,     'allreset': self.allreset, 'makemask': self.makemask}

        print Interpreter.GREEN_COLOR + '''
        =========  ==         =========  ==         ==     ==
        ==         ==         ==         == ==      ===    ==
        ==   ====  ==         =========  ======     == === ==
        ==     ==  =========  ==         ==   ==    ==    ===
        =========  =========  =========  ==     ==  ==     ==
        ''' + Interpreter.CLEAR_COLOR
        print 'This is {0} ver. {1} created by {2}.'.format(Interpreter.NAME, Interpreter.VERSION, Interpreter.CREATOR)
        print 'If you find any bugs, please report them to {}.\n'.format(Interpreter.CONTACT)

    @classmethod
    def error(cls, err):
        print Interpreter.RED_COLOR + 'Interpreter error: ' + Interpreter.CLEAR_COLOR + err

    def start(self):
        try:
            i = 1
            while True:
                command = raw_input(Interpreter.SYMBOL.format(i)).split()
                if len(command) == 0:
                    pass
                else:
                    comname, params = command[0], command[1:]
                    self.send_command(comname, params)
                i += 1
                print ''
        except End:
            print 'Bye!'

    def send_command(self, comname, params):
        if comname.startswith('#'):
            pass
        elif comname.startswith('?') or comname.endswith('?'):
            comname = comname.lstrip('?')
            comname = comname.rstrip('?')
            if comname in self.functions:
                help(self.functions[comname])
            else:
                err = '{} is not a valid command.'.format(Interpreter.YELLOW_COLOR + comname + Interpreter.CLEAR_COLOR)
                Interpreter.error(err)
        else:
            if comname in self.functions:
                self.functions[comname](params)
            else:
                err = '{} is not a valid command.'.format(Interpreter.YELLOW_COLOR + comname + Interpreter.CLEAR_COLOR)
                Interpreter.error(err)

    def extract_option(self, params):
        if Interpreter.IMG_OPTION in params:
            params.remove(Interpreter.IMG_OPTION)
            return Interpreter.IMG_OPTION
        elif Interpreter.SRC_OPTION in params:
            params.remove(Interpreter.SRC_OPTION)
            return Interpreter.SRC_OPTION
        elif Interpreter.IMGSRC_OPTION in params:
            params.remove(Interpreter.IMGSRC_OPTION)
            return Interpreter.IMGSRC_OPTION
        elif Interpreter.MDL_OPTION in params:
            params.remove(Interpreter.MDL_OPTION)
            return Interpreter.MDL_OPTION
        else:
            return None

    def quit(self, params):
        raise End()

    def go(self, params):
        self.glean.execute(phase=1)

    def gogo(self, params):
        self.glean.execute(phase=2)

    def get(self, params):
        option = self.extract_option(params)
        if len(params) != 1:
            Interpreter.error('The number of arguments is bad.')
            return Interpreter.ERROR_CODE

        if option == Interpreter.IMG_OPTION:
            value = self.glafic_i.params[params[0]]
        elif option == Interpreter.SRC_OPTION:
            value = self.glafic_s.params[params[0]]
        # elif option == '-is':
        #     value = OrderedDict()
        #     value['image']  = self.glafic_i.params[params[0]]
        #     value['source'] = self.glafic_s.params[params[0]]
        elif option == Interpreter.MDL_OPTION:
            value = self.glafic_i.models[params[0]]
        else:
            value = self.glean.params[params[0]]

        if not value:
            return Interpreter.ERROR_CODE

        # when 'all', 'primary', or 'secondary' are specified
        if isinstance(value, OrderedDict):
            for k, v in value.iteritems():
                print '{:<25} = {}'.format(Interpreter.YELLOW_COLOR + k + Interpreter.CLEAR_COLOR, v)
        # when '-m' is specified
        elif isinstance(value, list):
            for i, v in enumerate(value):
                print '#{} {}:'.format(i+1, v.name)
                for kk, vv in v.params.iteritems():
                    print '\t{:<20} = {}'.format(Interpreter.YELLOW_COLOR + kk + Interpreter.CLEAR_COLOR, vv)
        else:
            print value

    def set(self, params):
        option = self.extract_option(params)
        if len(params) != 2:
            Interpreter.error('The number of arguments is bad.')
            return Interpreter.ERROR_CODE

        if option == Interpreter.IMG_OPTION:
            self.glafic_i.params[params[0]] = params[1]
        elif option == Interpreter.SRC_OPTION:
            self.glafic_s.params[params[0]] = params[1]
        elif option == Interpreter.IMGSRC_OPTION:
            self.glafic_i.params[params[0]] = params[1]
            self.glafic_s.params[params[0]] = params[1]
        else:
            self.glean.params[params[0]] = params[1]            

    def reset(self, params):
        option = self.extract_option(params)
        if len(params) != 1:
            Interpreter.error('The number of arguments is bad.')
            return Interpreter.ERROR_CODE

        if option == Interpreter.IMG_OPTION:
            self.glafic_i.params.reset(params[0])
        elif option == Interpreter.SRC_OPTION:
            self.glafic_s.params.reset(params[0])
        elif option == Interpreter.IMGSRC_OPTION:
            self.glafic_i.params.reset(params[0])
            self.glafic_s.params.reset(params[0])
        elif option == Interpreter.MDL_OPTION:
            self.glafic_i.models.reset(params[0])
            self.glafic_s.models.reset(params[0])
        else:
            self.glean.params.reset(params[0])

    def allreset(self, params):
        self.glafic_i.params.reset('all')
        self.glafic_i.models.reset('all')
        self.glafic_s.params.reset('all')
        self.glafic_s.models.reset('all')
        self.glean.params.reset('all')

    def append(self, params):
        if len(params) >= 1:
            key    = params[0]
            params = params[1:]
            
            self.glafic_i.models.append(key, list(params))
            self.glafic_s.models.append(key, list(params))
        else:
            Interpreter.error('The number of arguments is bad.')

    def makemask(self, params):
        if len(params) >= 2:
            # to be implemented
            self.glean.makemask(params)
        else:
            Interpreter.error('The number of arguments is bad.')

    def clear(self, params):
        os.system('clear')

    def pwd(self, params):
        os.system('pwd')

    def cd(self, params):
        if len(params) == 0:
            os.chdir(os.path.expanduser('~/'))
        else:
            os.chdir(params[0])

    def ls(self, params):
        command = 'ls -FG' + ' ' + ' '.join(params)
        os.system(command)

    def open(self, params):
        command = 'open' + ' ' + ' '.join(params)
        os.system(command)

    def less(self, params):
        command = 'less' + ' ' + ' '.join(params)
        os.system(command)

    def more(self, params):
        command = 'more' + ' ' + ' '.join(params)
        os.system(command)

    def rm(self, params):
        command = 'rm -i' + ' ' + ' '.join(params)
        os.system(command)

    def read(self, params):
        try:
            f = open(params[0], 'r')
        except IndexError:
            Interpreter.error('Enter the name of a file.')
        except IOError:
            err = '{} does not exist.'.format(Interpreter.YELLOW_COLOR + params[0] + Interpreter.CLEAR_COLOR)
            Interpreter.error(err)
        else:
            for _command in f:
                command = _command.split()
                if len(command) == 0:
                    pass
                else:
                    comname, params = command[0], command[1:]
                    self.send_command(comname, params)
            f.close()

    # def plot2D(self, params):
    #     option = self.extract_option(params)
    #     if option == '-i':
    #         self.glean.beam.plot2D('image')
    #     elif option == '-s':
    #         self.glean.beam.plot2D('source')

    # def plot3D(self, params):
    #     option = self.extract_option(params)
    #     if option == '-i':
    #         self.glean.beam.plot3D('image')
    #     elif option == '-s':
    #         self.glean.beam.plot3D('source')
