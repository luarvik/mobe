import tornado.ioloop
import tornado.web
import operator
import cgi
import logging
import os
import sys
import sqlite3
import inspect
import datetime


'''
                          We implement our server as a state machine
                          This is the interface class for this machine
'''
class QueryStateMachine:
    def __init__(self):

        self.newState(DisconnectedState)

    def newState(self,new_state):
        self.state = new_state
        
    ''' The followed are the methods describing transitions between states
    '''  
    
    def connect(self):
        return self.state.connect(self)
        
    def disconnect(self):
        return self.state.disconnect(self)
                          
    def login(self,parameters):
        return self.state.login(parameters)
        
    def save(self,parameters):
        return self.state.save(parameters)
        
    def activity(self,parameters):
        return self.state.activity(self)  
        
   
        
'''                                State base abstract class                                 '''      
class QueryState:
    
    @staticmethod
    def connect(db_path,database):
        raise NotImplementedError()  

    @staticmethod
    def disconnect(connection):
        raise NotImplementedError()        

    @staticmethod   
    def login(parameters):
        raise NotImplementedError()   
        
    @staticmethod
    def save(parameters):
        raise NotImplementedError()   
        
    @staticmethod
    def activity(parameters):
        raise NotImplementedError()

      
        
'''                             Implementation of various states                                  '''

''' Sign out state. We disconnected from DB server and logged out from website '''
class DisconnectedState(QueryState):
    
    @staticmethod
    def connect(db_path,database):
        db = os.path.join(db_path,database)
        connection = sqlite3.connect(db)
        return connection

''' In this state, we are connected to the database   '''    
class ConnectedState(QueryState):
    @staticmethod
    def disconnect(connection):
        if (connection!=None):
            connection.close()
        
    @staticmethod
    def login(parameters):
                    
        connection = parameters['connection']
        user = parameters['user']
        passwd_hash = parameters['password_hash'].replace('/','')
        is_logged = False
        cursor = connection.cursor()                
        sql = "SELECT COUNT(id)  FROM users WHERE name='"+user+"' AND passwd_hash='"+passwd_hash+"'" 
        cursor.execute(sql) 
        query_data = cursor.fetchall()
        if (query_data[0][0]==1):
            is_logged = True
            print "Logged successfully"
        else:
            print "Unknown login or password"    
        return is_logged
        

''' In this state, we are logged to the website, i.e. we are able to create and save our web forms   '''  
class LoggedState(QueryState):

    @staticmethod
    def save(parameters):
        print "save called"
        data_storage_path = os.path.abspath('/home/ubuntu/form_builder/data/') # ./data
        fh = open(os.path.join(data_storage_path,'user.dat'),'w') 
        output_string = "500,"+str(datetime.datetime.now())+'\n' 
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


    @staticmethod
    def activity(parameters):  
        data_storage_path = os.path.abspath('/home/ubuntu/form_builder/data/') # ./data
        fh = open(os.path.join(data_storage_path,'user.dat'),'r')  
        types = {"10":"Button", "20":"Text", "30":"Checkbox",}
        activity = ""
        for line in fh:
            params = line.split(',')
            if params[0]=="500":
                activity+="Date and time:"+params[1]+";"
                continue
            activity+=types[params[0]]+":left="+params[1]+";top="+params[2]+'\n'
        fh.close()           
        return activity 

        
                  
                      
#---------------------------------------------------------------------------------------------

class MainHandler(tornado.web.RequestHandler):

    '''     Method to perform transition between machine states
            Return value is a callable metod that defines new state of the machine '''

    def getMachineStateMethod(self):
        
        handlers = {"user": "login",
                    "id": "save",
                    "dashboard": "activity",
                    "load": "pload",
        }
        method = None
        for key in handlers:
            if key in self.request.arguments:
                method = handlers[key]
                break

        return method

    ''' In the case we got a query to save form data, we must parse the form parameters first '''
    def save_parameters_dict(self):
        
        self.parameters['top'] = []
        self.parameters['left'] = []
        self.parameters['id'] = []

        for name in self.request.arguments:
            if name == 'end':
                continue
            args = self.get_query_arguments(name)    
            for arg in args:
                self.parameters[name].append(arg) 

    def login_parameters_dict(self):
        self.parameters['connection'] = self.connection
        self.parameters['user'] = self.get_argument("user")
        self.parameters['password_hash']  =  self.get_argument("password")   

    def page_loaded(self):   
        self.application.settings["state_machine"].newState(ConnectedState) 
        
    def show_machine_state(self):
        print "State machine: "+ str(self.application.settings["state_machine"].state).replace("__main__.","")   
                    
                     
    def get(self): 
        
        method = self.getMachineStateMethod()
        if (method is None):
            self.write("GET query to the tornado web server. It works.")
            return

        elif (method == "pload"): # page refresh event
            self.application.settings["state_machine"].newState(DisconnectedState)   
            return            
            
        self.parameters = dict()

        self.show_machine_state()
        
        machine_state = str(self.application.settings["state_machine"].state).replace("__main__.","")   
        if (machine_state == "DisconnectedState"):
            self.is_logged = False
            db_path = os.path.abspath('/home/ubuntu/form_builder/data/') # ./data
            db = os.path.join(db_path,'fbuilder')
            self.connection = self.application.settings["state_machine"].state.connect(db_path,db)  
            print self.connection 
            self.application.settings["state_machine"].newState(ConnectedState)

        self.show_machine_state() 
                                                    
        '''
        method = self.getMachineStateMethod()
        print method
        '''

        if (method == "save"):
            self.save_parameters_dict()
 
        
        elif (method == "login"):
            self.login_parameters_dict()
        
        data = getattr(self.application.settings["state_machine"],method)(self.parameters)
        
        if (method == "login"):
            self.is_logged = data
            print self.is_logged
            if (self.is_logged == True):
                self.set_status(200)
                self.application.settings["state_machine"].newState(LoggedState) 
                self.show_machine_state()
            else: 
                self.set_status(404)
                self.application.settings["state_machine"].state.disconnect(self.connection)
                self.application.settings["state_machine"].newState(DisconnectedState)  
                self.show_machine_state()
        elif(method == "activity"):
            self.write(data)         
               
  


def make_app():
    
    query_state_machine = QueryStateMachine()

    settings = {
        "static_path": os.path.join(os.path.dirname(__file__), 'builder'),
        "state_machine": query_state_machine,
    }	
   
    print  "HTTP server started."
    return tornado.web.Application([
        (r"/", MainHandler),
    ],**settings)	
    


if __name__ == "__main__":
    
    
    app = make_app()
    #print app.settings["state_machine"]
    app.listen(80)
    tornado.ioloop.IOLoop.current().start()
    
 


