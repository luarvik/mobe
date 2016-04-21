#!/usr/bin/env python2.7
# -*- coding: utf-8 -*-
'''
Web and database server for the form builder app
'''

VERSION = '1.2'

import argparse
import BaseHTTPServer
import cgi
import logging
import os
import sys
import sqlite3


def make_request_handler_class(opts):
    '''
    Factory to make the request handler and add arguments to it.

    It exists to allow the handler to access the opts.path variable
    locally.
    '''
    class MyRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
        '''
        Factory generated request handler class that contain
        additional class variables.
        '''
        m_opts = opts

        def do_HEAD(self):
            '''
            Handle a HEAD request.
            '''
            logging.debug('HEADER %s' % (self.path))
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
        
        '''
        We store users information in a SQLite database
        '''
        def retrieve_db_data(self):
            db_path = os.path.abspath('../data/')
            db = os.path.join(db_path,'fbuilder')  
            connection = sqlite3.connect(db)
            cursor = connection.cursor()
            cursor.execute('SELECT * FROM users')  
            print cursor.fetchall()            
            connection.close()        
            
            
                                                            
        '''
        We store the web form data created by an user as CSV file
        Path to this file is stored in SQLite database
        '''
        def save_data(self,args):         
            data_storage_path = os.path.abspath('../data/') 
            fh = open(os.path.join(data_storage_path,'user.dat'),'w')    
            params_count = len(args['id'])     
               
            i=0
            while (i<params_count):   
                output_string = ""                       
                output_string+= args['id'][i]+","
                output_string+= args['left'][i]+","
                output_string+= args['top'][i]+'\n'
                fh.write(output_string)
                                
                i+=1  
                              
            fh.close() 
            
        def check_login_data(self,user,passwd_hash):
            retvalue = 0
            db_path = os.path.abspath('../data/')
            db = os.path.join(db_path,'fbuilder')
            connection = sqlite3.connect(db)
            cursor = connection.cursor()                                                   
            cursor.execute("SELECT id  FROM users WHERE name='"+user+"' AND passwd_hash='"+passwd_hash+"'") 
            cursor_len =len(cursor.fetchall()) 
            connection.close() 
            if (cursor_len>0):
                logging.debug("Logged successfully")
                retvalue=1
            return retvalue                                        



        def do_GET(self):
            '''
            Handle a GET request.
            '''
            logging.debug('GET  %s' % (self.path))

            # Parse out the arguments.
            # The arguments follow a '?' in the URL. Here is an example:
            #   http://example.com?arg1=val1
            args = {}
            idx = self.path.find('?')
            left = self.path.find('left')
            if idx >= 0:
                rpath = self.path[:idx]
                args = cgi.parse_qs(self.path[idx+1:])
            else:
                rpath = self.path
            
            if left >= 0:
                self.save_data(args)
            else:
                user_exists = self.check_login_data(args['user'][0],args['password'][0])
                if (user_exists):
                    self.send_response(200)
                else:
                    self.send_response(404)                    

            # Print out logging information about the path and args.
            if 'content-type' in self.headers:
                ctype, _ = cgi.parse_header(self.headers['content-type'])
                logging.debug('TYPE %s' % (ctype))

            logging.debug('PATH %s' % (rpath))
            logging.debug('ARGS %d' % (len(args)))
            if len(args):
                i = 0
                for key in sorted(args):
                    logging.debug('ARG[%d] %s=%s' % (i, key, args[key]))
                    i += 1

            # Check to see whether the file is stored locally,
            # if it is, display it.
            # There is special handling for http://127.0.0.1/info. That URL
            # displays some internal information.
            if self.path == '/info' or self.path == '/info/':
                self.send_response(200)  # OK
                self.send_header('Content-type', 'text/html')
                self.end_headers()
            
            else:
                # Get the file path.
                path = MyRequestHandler.m_opts.rootdir + rpath
                dirpath = None
                logging.debug('FILE %s' % (path))

                # If it is a directory look for index.html
                # or process it directly if there are 3
                # trailing slashed.
                if rpath[-3:] == '///':
                    dirpath = path
                elif os.path.exists(path) and os.path.isdir(path):
                    dirpath = path  # the directory portion
                    index_files = ['/index.html', '/index.htm', ]
                    for index_file in index_files:
                        tmppath = path + index_file
                        if os.path.exists(tmppath):
                            path = tmppath
                            break

                # Allow the user to type "///" at the end to see the
                # directory listing.
                if os.path.exists(path) and os.path.isfile(path):
                    # This is valid file, send it as the response
                    # after determining whether it is a type that
                    # the server recognizes.
                    _, ext = os.path.splitext(path)
                    ext = ext.lower()
                    content_type = {
                        '.css': 'text/css',
                        '.gif': 'image/gif',
                        '.htm': 'text/html',
                        '.html': 'text/html',
                        '.jpeg': 'image/jpeg',
                        '.jpg': 'image/jpg',
                        '.js': 'text/javascript',
                        '.png': 'image/png',
                        '.text': 'text/plain',
                        '.txt': 'text/plain',
                    }

                    # If it is a known extension, set the correct
                    # content type in the response.
                    if ext in content_type:
                        self.send_response(200)  # OK
                        self.send_header('Content-type', content_type[ext])
                        self.end_headers()

                        with open(path) as ifp:
                            self.wfile.write(ifp.read())
                    else:
                        # Unknown file type or a directory.
                        # Treat it as plain text.
                        self.send_response(200)  # OK
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()

                        with open(path) as ifp:
                            self.wfile.write(ifp.read())
                else:
                    if dirpath is None or self.m_opts.no_dirlist == True:
                        # Invalid file path, respond with a server access error
                        self.send_response(500)  # generic server error for now
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()

                        self.wfile.write('<html>')
                        self.wfile.write('  <head>')
                        self.wfile.write('    <title>Server Access Error</title>')
                        self.wfile.write('  </head>')
                        self.wfile.write('  <body>')
                        self.wfile.write('    <p>Server access error.</p>')
                        self.wfile.write('    <p>%r</p>' % (repr(self.path)))
                        self.wfile.write('    <p><a href="%s">Back</a></p>' % (rpath))
                        self.wfile.write('  </body>')
                        self.wfile.write('</html>')
                    else:
                        # List the directory contents. Allow simple navigation.
                        logging.debug('DIR %s' % (dirpath))

                        self.send_response(200)  # OK
                        self.send_header('Content-type', 'text/html')
                        self.end_headers()
                        
                        self.wfile.write('<html>')
                        self.wfile.write('  <head>')
                        self.wfile.write('    <title>%s</title>' % (dirpath))
                        self.wfile.write('  </head>')
                        self.wfile.write('  <body>')
                        self.wfile.write('    <a href="%s">Home</a><br>' % ('/'));

                        # Make the directory path navigable.
                        dirstr = ''
                        href = None
                        for seg in rpath.split('/'):
                            if href is None:
                                href = seg
                            else:
                                href = href + '/' + seg
                                dirstr += '/'
                            dirstr += '<a href="%s">%s</a>' % (href, seg)
                        self.wfile.write('    <p>Directory: %s</p>' % (dirstr))

                        # Write out the simple directory list (name and size).
                        self.wfile.write('    <table border="0">')
                        self.wfile.write('      <tbody>')
                        fnames = ['..']
                        fnames.extend(sorted(os.listdir(dirpath), key=str.lower))
                        for fname in fnames:
                            self.wfile.write('        <tr>')
                            self.wfile.write('          <td align="left">')
                            path = rpath + '/' + fname
                            fpath = os.path.join(dirpath, fname)
                            if os.path.isdir(path):
                                self.wfile.write('            <a href="%s">%s/</a>' % (path, fname))
                            else:
                                self.wfile.write('            <a href="%s">%s</a>' % (path, fname))
                            self.wfile.write('          <td>&nbsp;&nbsp;</td>')
                            self.wfile.write('          </td>')
                            self.wfile.write('          <td align="right">%d</td>' % (os.path.getsize(fpath)))
                            self.wfile.write('        </tr>')
                        self.wfile.write('      </tbody>')
                        self.wfile.write('    </table>')
                        self.wfile.write('  </body>')
                        self.wfile.write('</html>')

        def do_POST(self):
            '''
            Handle POST requests.
            '''
            logging.debug('POST %s' % (self.path))

            # CITATION: http://stackoverflow.com/questions/4233218/python-basehttprequesthandler-post-variables
            ctype, pdict = cgi.parse_header(self.headers['content-type'])
            if ctype == 'multipart/form-data':
                postvars = cgi.parse_multipart(self.rfile, pdict)
            elif ctype == 'application/x-www-form-urlencoded':
                length = int(self.headers['content-length'])
                postvars = cgi.parse_qs(self.rfile.read(length), keep_blank_values=1)
            else:
                postvars = {}

            # Get the "Back" link.
            back = self.path if self.path.find('?') < 0 else self.path[:self.path.find('?')]

            # Print out logging information about the path and args.
            logging.debug('TYPE %s' % (ctype))
            logging.debug('PATH %s' % (self.path))
            logging.debug('ARGS %d' % (len(postvars)))
            if len(postvars):
                i = 0
                for key in sorted(postvars):
                    logging.debug('ARG[%d] %s=%s' % (i, key, postvars[key]))
                    i += 1

            # Tell the browser everything is okay and that there is
            # HTML to display.
            self.send_response(200)  # OK
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Display the POST variables.
            self.wfile.write('<html>')
            self.wfile.write('  <head>')
            self.wfile.write('    <title>Server POST Response</title>')
            self.wfile.write('  </head>')
            self.wfile.write('  <body>')
            self.wfile.write('    <p>POST variables (%d).</p>' % (len(postvars)))

            if len(postvars):
                # Write out the POST variables in 3 columns.
                self.wfile.write('    <table>')
                self.wfile.write('      <tbody>')
                i = 0
                for key in sorted(postvars):
                    i += 1
                    val = postvars[key]
                    self.wfile.write('        <tr>')
                    self.wfile.write('          <td align="right">%d</td>' % (i))
                    self.wfile.write('          <td align="right">%s</td>' % key)
                    self.wfile.write('          <td align="left">%s</td>' % val)
                    self.wfile.write('        </tr>')
                self.wfile.write('      </tbody>')
                self.wfile.write('    </table>')

            self.wfile.write('    <p><a href="%s">Back</a></p>' % (back))
            self.wfile.write('  </body>')
            self.wfile.write('</html>')

    return MyRequestHandler


def err(msg):
    '''
    Report an error message and exit.
    '''
    print('ERROR: %s' % (msg))
    sys.exit(1)


def getopts():
    '''
    Get the command line options.
    '''

    # Get the help from the module documentation.
    this = os.path.basename(sys.argv[0])
    description = ('description:%s' % '\n  '.join(__doc__.split('\n')))
    epilog = ' '
    rawd = argparse.RawDescriptionHelpFormatter
    parser = argparse.ArgumentParser(formatter_class=rawd,
                                     description=description,
                                     epilog=epilog)

    parser.add_argument('-H', '--host',
                        action='store',
                        type=str,
                        default='127.0.0.1',
                        help='hostname, default=%(default)s')

    parser.add_argument('-l', '--level',
                        action='store',
                        type=str,
                        default='debug',
                        choices=['notset', 'debug', 'info', 'warning', 'error', 'critical',],
                        help='define the logging level, the default is %(default)s')

    parser.add_argument('--no-dirlist',
                        action='store_true',
                        help='disable directory listings')

    parser.add_argument('-p', '--port',
                        action='store',
                        type=int,
                        default=8888,
                        help='port, default=%(default)s')

    parser.add_argument('-r', '--rootdir',
                        action='store',
                        type=str,
                        default=os.path.abspath('..'),
                        help='web directory root that contains the HTML/CSS/JS files %(default)s')

    parser.add_argument('-v', '--verbose',
                        action='count',
                        help='level of verbosity')

    

    opts = parser.parse_args()
    opts.rootdir = os.path.abspath(opts.rootdir)
    if not os.path.isdir(opts.rootdir):
        err('Root directory does not exist: ' + opts.rootdir)
    if opts.port < 1 or opts.port > 65535:
        err('Port is out of range [1..65535]: %d' % (opts.port))
    return opts


def httpd(opts):
    '''
    HTTP server
    '''
    RequestHandlerClass = make_request_handler_class(opts)
    server = BaseHTTPServer.HTTPServer((opts.host, opts.port), RequestHandlerClass)
    logging.info('Server starting %s:%s (level=%s)' % (opts.host, opts.port, opts.level))
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    server.server_close()
    logging.info('Server stopping %s:%s' % (opts.host, opts.port))


def get_logging_level(opts):
    '''
    Get the logging levels specified on the command line.
    The level can only be set once.
    '''
    if opts.level == 'notset':
        return logging.NOTSET
    elif opts.level == 'debug':
        return logging.DEBUG
    elif opts.level == 'info':
        return logging.INFO
    elif opts.level == 'warning':
        return logging.WARNING
    elif opts.level == 'error':
        return logging.ERROR
    elif opts.level == 'critical':
        return logging.CRITICAL



def main():
    ''' main entry '''
    opts = getopts()
    #if opts.daemonize:
        #daemonize(opts)
    logging.basicConfig(format='%(asctime)s [%(levelname)s] %(message)s', level=get_logging_level(opts))
    httpd(opts)


if __name__ == '__main__':
    main()  # this allows library functionality
