import tornado.ioloop
import tornado.web
import cgi
import logging
import os
import sys
import sqlite3

class MainHandler(tornado.web.RequestHandler):
    def get(self): 
        parameters = dict()                             
        parameters['top'] = []
        parameters['left'] = []
        parameters['id'] = []
        
        if 'user' in  self.request.arguments:      # login query processing    
            is_logged = self.check_login_data(self.get_argument("user"),self.get_argument("password").replace('/',''))     
            if is_logged == 1:
                self.set_status(200)  
            else:
                self.set_status(404)
                
        elif 'dashboard' in  self.request.arguments:
            print "Dashboard data request" 
            dashboard_data = self.read_dashboard_data()
            print dashboard_data
            self.write(dashboard_data)
                    
        else:                                      # save user form data on database
            print self.request 

            def save_data():
                data_storage_path = os.path.abspath('./data/') 
                fh = open(os.path.join(data_storage_path,'user.dat'),'w') 
                output_string = ""
                def build_output_string():
                    elements_last_idx = len(parameters['top'])-1
                    s=""
                    while elements_last_idx>=0:
                        s += parameters['id'][elements_last_idx]+','
                        s += parameters['left'][elements_last_idx]+','
                        s += parameters['top'][elements_last_idx]+'\n'
                        elements_last_idx-=1 
                        yield s
                        s = ""
                
                for st in build_output_string():
                    output_string+=st
                print "output string:"+output_string    
                fh.write(output_string)    
                fh.close()
                    
            for name in self.request.arguments: 
                if name == 'end':
                    continue                                  
                args = self.get_query_arguments(name)
                for arg in args:
                    parameters[name].append(arg)                                             
            save_data()
             
    def read_dashboard_data(self):
        data_storage_path = os.path.abspath('./data/')         
        fh = open(os.path.join(data_storage_path,'user.dat'),'r')       
        types = {"10":"Button", "20":"Text", "30":"Checkbox",}
        outstr = ""
        for line in fh:
            params = line.split(',')
           
            outstr+=types[params[0]]+":left="+params[1]+";top="+params[2]+'\n'
        fh.close()
        return outstr

    def check_login_data(self,user,passwd_hash):
        retvalue = 0
        db_path = os.path.abspath('./data/')
        db = os.path.join(db_path,'fbuilder')
        connection = sqlite3.connect(db)
        cursor = connection.cursor()     
        sql = "SELECT COUNT(id)  FROM users WHERE name='"+user+"' AND passwd_hash='"+passwd_hash+"'"                                             
        cursor.execute(sql) 
        logging.debug(sql)
        query_data = cursor.fetchall()
        logging.debug(query_data)
        connection.close() 
        if (query_data[0][0]==1):
            print("Logged successfully")
            retvalue=1
        return retvalue  
        
                     

def make_app():
    
    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), 'builder'),
    }	
    #print settings["static_path"]
    print  "HTTP server started."
    return tornado.web.Application([
        (r"/", MainHandler),
    ],**settings)	
  	

if __name__ == "__main__":
    app = make_app()
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()


