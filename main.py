from kivy.app import App
from kivy.uix.widget import Widget
from kivy.uix.button import Button
from kivy.uix.floatlayout import FloatLayout
from kivy.properties import NumericProperty, ReferenceListProperty,\
    ObjectProperty
from functools import partial
from kivy.clock import Clock
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.lang import Builder
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.storage.jsonstore import JsonStore
from kivy.uix.popup import Popup
import pymysql
import pysftp

#connect to the database and make a cursor.
#password removed
db = pymysql.connect(host="sql9.freemysqlhosting.net",database="sql9213958",user="sql9213958", password = "", port = 3306)
cursor = db.cursor()

loggedUser = ""

#connect to the remote file server with sftp
#password removed
cnopts = pysftp.CnOpts()
cnopts.hostkeys = None 
sftp = pysftp.Connection('ssh.phx.nearlyfreespeech.net', username='odavidson707_owenldavidson', password='', cnopts = cnopts)

class TasksWindow(Screen):
    def __init__(self, isRoot, parScreen, parList, parListIndex, doPut):
        global store
        global screenCounter
        store.put('screenCounter', val= screenCounter)
        store.put('taskCounter',val = taskCounter)
        if doPut:
            with sftp.cd('/home/public/taskapp/'):
                sftp.put(r'''C:\Users\Owen\Desktop\\Owens Generic Task App\%s.json'''%loggedUser)
        super(TasksWindow, self).__init__()
        self.btnHeight=[]
        self.btnHeight.append(.9)
        self.btnList = []
        self.isRoot = isRoot
        self.parScreen = parScreen
        self.parList = parList
        self.parListIndex = parListIndex
        addBtn = Button(text = "+",pos_hint= {'x': .9,'top': .7},size_hint = (.1,.1))
        addBtn.bind(on_press=self.clkAdd)
        self.add_widget(addBtn)
        #if this is a subtask, write some filler text and then shift everything down.
        if self.isRoot == False:
            backBtn = Button(text = "Go Back",pos_hint= {'x': 0,'top': 1},size_hint = (.1,.1))
            backBtn.bind(on_press=self.clkBack)
            textinput = TextInput(text='Enter name of task', pos_hint={'x': 0,'top': .9},size_hint = (1,.1),  multiline=False)
            textinput.bind(on_text_validate=self.onEnter)
            shareBtn = Button(text = "Share this task",pos_hint= {'x': .7,'top': 1},size_hint = (.3,.1))
            shareBtn.bind(on_press=self.clkShare)
            #filler = Label(text = "Angela, Pamela, Sandra and Rita.",pos_hint= {'x': 0,'top': .9},size_hint = (1,.2))
            #self.add_widget(filler)
            self.add_widget(backBtn)
            self.add_widget(textinput)

    def onEnter(instance, value):
        global store
        nameBtn = Button(text = value.text,pos_hint= {'x': 0,'top': .9},size_hint = (1,.1))
        nameBtn.bind(on_press=instance.clkName)
        instance.remove_widget(value)
        instance.add_widget(nameBtn)
        instance.parList[instance.parListIndex].editBtn.text = value.text
        shList ="".join(instance.parList[instance.parListIndex].sharedList)
        store.put ('Task %d' % instance.parList[instance.parListIndex].taskNum, parScreen= store.get('Task %d' % instance.parList[instance.parListIndex].taskNum)['parScreen'], text = value.text, childScreen = sm.current, sharedList = shList)
        with sftp.cd('/home/public/taskapp/'):
            sftp.put(r'''C:\Users\Owen\Desktop\\Owens Generic Task App\%s.json'''%loggedUser)
            
    def clkName(self, obj):
        textinput = TextInput(text=obj.text, pos_hint={'x': 0,'top': .9},size_hint = (1,.1),  multiline=False)
        textinput.bind(on_text_validate=self.onEnter)
        self.remove_widget(obj)
        self.add_widget(textinput)
        
        #= Button(text = textinput.text ,pos_hint= {'x': 0,'top': .9-.1 *parListIndex},size_hint = (.9,.1))

    def clkAdd(self, obj):
        task = Task(self.btnHeight, self.btnList, self.isRoot, "Tap to Edit", "No Child", True, -1, {loggedUser})

    def clkBack(self, obj):
        sm.current = self.parScreen

    def clkShare(self, obj):
        temp = sm.current_screen
        tempName = sm.current
        sm.current = 'Share Screen'
        sm.current_screen.update(self.parList[self.parListIndex], temp, tempName)

    def update(self):
        for x in range (0, len(self.btnList)):
            temp = self.btnList.pop(x)
            if (x == 0):
                if self.isRoot == True:
                    self.btnHeight[0] = .9
                else:
                    self.btnHeight[0] = .6
            temp2 = Task(self.btnHeight, self.btnList, self.isRoot, temp.editBtn.text, temp.childScreen, False, temp.taskNum, temp.sharedList)
            #print ("Adding task with text", temp.editBtn.text)
            temp2.alreadyAdded = True
            if (x == len(self.btnList)-1):
                self.repaint = False
            self.btnList.insert(x,temp2)
            del(self.btnList[len(self.btnList)-1])
            self.add_widget(temp2.editBtn)
            self.add_widget(temp2.delBtn)

    def preupdate(self,dt):
        tempList = []
        bPoint = -1
        for x in range (0, len(self.btnList)):
            tempList.append(self.btnList[x])
        for x in range (0, len(self.btnList)):
            temp = self.btnList.pop(x)
            self.remove_widget(temp.editBtn)
            self.remove_widget(temp.delBtn)
            if temp.disp == True:
                self.btnList.insert(x, temp)
            else:
                if len(self.btnList) != 0:
                    bPoint = x
                    break
        if bPoint != -1:
            for x in range (bPoint-1, len(self.btnList)):
                temp = self.btnList.pop(x)
                self.remove_widget(temp.editBtn)
                self.remove_widget(temp.delBtn)
                self.btnList.insert(x, temp)
        self.update()

    def loadData(self):
        print("loadData called")
        if store.get("taskCounter")['val'] != 0 | store.exists("Task 0"):
                for item in store.find(parScreen=sm.current):
                    data = item[0].split()
                    sharedList = store.get(item[0])['sharedList'].split(",")
                    if sm.current == 'Screen 0':
                        newTask = Task(self.btnHeight, self.btnList, True, store.get(item[0])['text'], store.get(item[0])['childScreen'],False,int(data[1]), sharedList)
                    else:
                        newTask = Task(self.btnHeight, self.btnList, False, store.get(item[0])['text'], store.get(item[0])['childScreen'],False,int(data[1]), sharedList)
                    #print ("Creating task in ", sm.current, " With text ", store.get(item[0])['text'])
                    if store.get(item[0])['childScreen'] != 'No Child':
                        screen = TasksWindow(False, store.get(item[0])['parScreen'], self.btnList, self.btnList.index(newTask), True)
                        screen.name = store.get(item[0])['childScreen']
                        Clock.schedule_interval(screen.preupdate, 1.0/2.0)
                        test = Label(text = "Angela, Pamela, Sandra and Rita.",pos_hint= {'x': 0,'top': .8},size_hint = (1,.1))
                        screen.add_widget(test)
                        sm.add_widget(screen)
                        sm.current = store.get(item[0])['childScreen']
                        screen.loadData()
                        sm.current = store.get(item[0])['parScreen']
class LoginScreen(Screen):
    def __init__(self):
        super(LoginScreen, self).__init__()
        self.userinput = TextInput(text='Enter your username',pos_hint={'x': 0,'top': .9}, size_hint = (1,.1),  multiline=False)
        #userinput.bind(on_text_validate=self.onEnterUser)
        self.add_widget(self.userinput)
        self.passinput = TextInput(text='Enter your password', pos_hint={'x': 0,'top': .8},size_hint = (1,.1),  multiline=False)
        self.add_widget(self.passinput)
        self.newuser = Button(text='No account? Tap to create one.', pos_hint={'x': .25,'top': .6},size_hint = (.5,.1))
        self.newuser.bind(on_press = self.clkNewUser)
        self.add_widget(self.newuser)
        self.loginBtn = Button(text='Click to Login', pos_hint={'x': .25,'top': .7},size_hint = (.5,.1))
        self.loginBtn.bind(on_press = self.clkLogin)
        self.add_widget(self.loginBtn)

    def clkNewUser (self, obj):
        accScreen = AccScreen()
        accScreen.name = 'Acc Screen'
        sm.add_widget(accScreen)
        sm.current = 'Acc Screen'
        
    def clkLogin (self, obj):
        global db
        global cursor
        global loggedUser
        global sftp
        global store
        global screenCounter
        global taskCounter
        sql = "SELECT * FROM USERS \
        WHERE USER = '%s' AND PW = '%s'" % (self.userinput.text, self.passinput.text)
        cursor.execute(sql)
        db.commit()
        results = cursor.fetchall()
        if not results:
            popup = Popup(title='Login mismatch',
                          content=Label(text='Your password may be incorrect or the account may not exist.  Please try again or else create an account.'),
                          size_hint=(.8, .5))
            popup.open()
        else:
            loggedUser = self.userinput.text
            popup = Popup(title='Login successful',
                          content=Label(text='You have logged in successfully'),
                          size_hint=(.5, .5))
            popup.open()
            #check if there exists a file named 'loggedUser.json'
            with sftp.cd('/home/public/taskapp/'):
                exists = sftp.isfile('%s.json'% loggedUser)
            #if there does not, store = loggedUser.json.  This will be an empty file for a new user.
            if not exists:
                store = JsonStore('%s.json' % loggedUser)
                screenCounter = 0
                taskCounter = 0
            #if there is, get that file and then set store equal to it.
            else:
                sftp.get('/home/public/taskapp/%s.json'%loggedUser)
                store = JsonStore('%s.json' % loggedUser)
                if store.exists('screenCounter'):
                    screenCounter = store.get('screenCounter')['val']
                else:
                    screenCounter= 0
                if store.exists('taskCounter'):
                    taskCounter = store.get('taskCounter')['val']
                else:
                    taskCounter = 0
            screen = TasksWindow(True, 'No Parent', [], -1, True)
            screen.name = 'Screen 0'
            Clock.schedule_interval(screen.preupdate, 1.0/2.0)
            sm.add_widget(screen)
            sm.current = 'Screen 0'
            screen.loadData()

class AccScreen(Screen):
    def __init__(self):
        super(AccScreen, self).__init__()
        backBtn = Button(text = "Go Back",pos_hint= {'x': 0,'top': 1},size_hint = (.1,.1))
        backBtn.bind(on_press=self.clkBack)
        self.userinput = TextInput(text='Enter your desired username', pos_hint={'x': 0,'top': .8},size_hint = (1,.1),  multiline=False)
        self.passinput = TextInput(text='Enter your desired password', pos_hint={'x': 0,'top': .7},size_hint = (1,.1),  multiline=False)
        self.passconfirm = TextInput(text='Confirm your desired password', pos_hint={'x': 0,'top': .6},size_hint = (1,.1),  multiline=False)
        self.confirmBtn = Button(text='Click to create account', pos_hint={'x': .25,'top': .5},size_hint = (.5,.1))
        self.confirmBtn.bind(on_press=self.clkConfirm)
        self.add_widget(backBtn)
        self.add_widget(self.userinput)
        self.add_widget(self.passinput)
        self.add_widget(self.passconfirm)
        self.add_widget(self.confirmBtn)

    def clkBack (self,obj):
        sm.current = 'Login Screen'

    def clkConfirm (self, obj):
        if len(self.userinput.text) > 20 | len(self.passinput.text) > 20:
            popup = Popup(title='Password or username too long',
                          content=Label(text='Usernames and passwords may only be 20 characters'),
                          size_hint=(.5, .5))
            popup.open()
            return
        if self.passinput.text != self.passconfirm.text:
            popup = Popup(title='Passwords do not match',
                          content=Label(text='Re-enter your passwords.'),
                          size_hint=(.5, .5))
            popup.open()
            return
        sql = "SELECT * FROM USERS \
        WHERE USER = '%s'" % (self.userinput.text)
        cursor.execute(sql)
        results = cursor.fetchall()
        if not results:
            sql = "INSERT INTO USERS (USER, PW) VALUES ('%s', '%s')" % \
                (self.userinput.text, self.passinput.text)
            cursor.execute(sql)
            popup = Popup(title='Account Created!',
                          content=Label(text='Go back to login.'),
                          size_hint=(.5, .5))
            popup.open()
        else:
            popup = Popup(title='Account exists',
                          content=Label(text='That account already exists.  If you have a forgotten your password, too bad.'),
                          size_hint=(.5, .5))
            popup.open()
            
class ShareScreen(Screen):
    def __init__ (self):
        #The share screen has a Label saying "These are the current people this task is shared with", a text input to enter or delete names, and a back button
        self.label = Label(text = "These are the current people this task is shared with:",pos_hint= {'x': 0,'top': .9},size_hint = (1,.1))
        backBtn = Button(text = "Go Back",pos_hint= {'x': 0,'top': 1},size_hint = (.1,.1))
        backBtn.bind(on_press=self.clkBack)
        self.add_widget(self.label)
        self.add_widget(backBtn)

    def update (self, parTask, prevScreen, prevScreenName):
        self.prevScreen = prevScreen
        self.prevScreenName = prevScreenName
        self.parTask = parTask
        labelHeight = .8
        for user in sharedList:
            userLabel = Label(text = user, pos_hint= {'x': 0,'top': labelHeight},size_hint = (.9,.1))
            delBtn = Button(text = "Unshare",pos_hint= {'x': .9,'top': labelHeight},size_hint = (.1,.1))
            labelHeight = labelHeight - .1
            self.add_widget(delBtn)
            self.add_widget(userLabel)
        self.newUser = TextInput(text='Enter name of task', pos_hint={'x': 0,'top': labelHeight},size_hint = (.9,.1),  multiline=False)
        self.newUser.bind(on_text_validate=self.clkShare)
        shareBtn = Button(text = "Share",pos_hint= {'x': .9,'top': labelHeight},size_hint = (.1,.1))
        shareBtn.bind(on_press=self.clkShare)
        self.add_widget(self.newUser)
        self.add_widget(shareBtn)        
        
    def clkBack (self,obj):
        sm.current = self.prevScreen

    def clkShare (self, obj):
        self.parTask.sharedList.append(self.newUser.text)
        self.adjustSharedList()

    def adjustSharedList (self):
        #First clear the prevScreen of widgets
        self.prevScreen.clear_widgets()
        #Then change all the shared lists in memory, in a fashion similar to recursiveDel
        shList = "".join(self.parTask.sharedList)
        self.recursiveShare("Task %d" % self.parTask.taskNum, store.get("Task %d" % self.parTask.taskNum)['childScreen'], shList)
        #Then loadData to repopulate tasks
        sm.current = self.prevScreenName
        prevScreen.loadData()
        sm.current = "Share Screen"
        #Then restore the buttons lost in the previous clear
        if not prevScreen.isRoot:
            backBtn = Button(text = "Go Back",pos_hint= {'x': 0,'top': 1},size_hint = (.1,.1))
            backBtn.bind(on_press=TasksWindow.clkBack)
            textinput = TextInput(text='Enter name of task', pos_hint={'x': 0,'top': .9},size_hint = (1,.1),  multiline=False)
            textinput.bind(on_text_validate=TasksWindow.onEnter)
        addBtn = Button(text = "+",pos_hint= {'x': .9,'top': .7},size_hint = (.1,.1))
        addBtn.bind(on_press=self.clkAdd)
        self.add_widget(addBtn)
        with sftp.cd('/home/public/taskapp/'):
                sftp.put(r'''C:\Users\Owen\Desktop\\Owens Generic Task App\%s.json'''%loggedUser)
    
class Task(TasksWindow):
    def __init__(self, btnHeight, btnList, isRoot, currentText, childScreen, newlyAdded, taskNum, sharedList):
        global screenCounter
        global taskCounter
        global store
        global sftp
        global loggedUser
        if newlyAdded:
            self.taskNum = taskCounter
        else:
            self.taskNum = taskNum
        self.btnList = btnList
        self.childScreen = childScreen
        self.currentText = currentText
        self.sharedList = sharedList
        #for x in range (len(self.btnList)):
            #print(self.btnList[x].currentText)
        if len(btnList)==0 and isRoot == True:
            btnHeight[0] = .9
        if len(btnList)==0 and isRoot == False:
            btnHeight[0] = .6
        self.editBtn = Button(text = currentText,pos_hint= {'x': 0,'top': btnHeight[0]},size_hint = (.9,.1))
        self.delBtn = Button(text = "X",pos_hint= {'x': .9,'top': btnHeight[0]},size_hint = (.1,.1))
        self.delBtn.bind(on_press=self.clkDel)
        self.editBtn.bind(on_press=self.clkEdit)
        self.disp = True
        #self.alreadyAdded = False
        if newlyAdded:
            print ("Why isn't it putting?")
            store.put('Task %d' % taskCounter, parScreen= sm.current, text = 'Tap to Edit', childScreen = "No Child", sharedList = loggedUser)
            taskCounter= taskCounter+1
            store.put('taskCounter', val = taskCounter)
            with sftp.cd('/home/public/taskapp/'):
                sftp.put(r'''C:\Users\Owen\Desktop\\Owens Generic Task App\%s.json'''%loggedUser)
        btnList.append(self)
        btnHeight[0] -= .1
        
    def clkDel(self,obj):
        global store
        self.disp = False
        self.recursiveDel("Task %d" % self.taskNum,store.get("Task %d" % self.taskNum)['childScreen'])
        with sftp.cd('/home/public/taskapp/'):
                sftp.put(r'''C:\Users\Owen\Desktop\\Owens Generic Task App\%s.json'''%loggedUser)
        #self.alreadyAdded = False
        #TasksWindow.repaint = True

    #recursively delete all tasks that are the children of the task to be deleted
    def recursiveDel(self, taskName, childScreen):
        global store
        #base case: this task has no children
        if childScreen == "No Child":
            store.delete(taskName)
        else:
            #recursive case: call this function for every task whose parent is the one you are trying to delete
            for item in list(store.find(parScreen=childScreen)):
                print("Is this doing anything?", item[0], "is the name of the task currently to be deleted")
                self.recursiveDel(item[0], store.get(item[0])['childScreen'])
            #once you have deleted all the children, delete the parent
            store.delete(taskName)

    #recursively change the shared lists tasks that are the children of this task
    def recursiveShare(self, taskName, childScreen, sharedList):
        #base case: this task has no children
        
        if childScreen == "No Child":
            store.put('Task %d' % self.taskNum, parScreen= store.get('Task %d' % self.taskNum)["parScreen"], text = store.get('Task %d' % self.taskNum)["text"], childScreen = store.get('Task %d' % self.taskNum)["childScreen"], sharedList = sharedList)
        else:
            #recursive case: call this function for every task whose parent is the one you are trying to delete
            for item in list(store.find(parScreen=childScreen)):
                print("Is this doing anything?", item[0], "is the name of the task currently to be deleted")
                self.recursiveShare(item[0], store.get(item[0])['childScreen'], sharedList)
            #once you have deleted all the children, delete the parent
            store.put('Task %d' % self.taskNum, parScreen= store.get('Task %d' % self.taskNum)["parScreen"], text = store.get('Task %d' % self.taskNum)["text"], childScreen = store.get('Task %d' % self.taskNum)["childScreen"], sharedList = sharedList)

    def clkEdit(self,obj):
        print (self.childScreen)
        global screenCounter
        if self.childScreen == "No Child":
            screenCounter = screenCounter + 1
            store.put('screenCounter', val= screenCounter)
            #print("Should be creating new screen and switching to it")
            screen = TasksWindow(False, sm.current, self.btnList, self.btnList.index(self), False)
            screen.name = ('Screen %d' % screenCounter)
            #print("New screen is named", 'Screen %d' % screenCounter)
            sm.add_widget(screen)
            parScr = sm.current
            sm.current = ('Screen %d' % screenCounter)
            self.childScreen = sm.current
            Clock.schedule_interval(screen.preupdate, 1.0/2.0)
            store.put('Task %d' % self.taskNum, parScreen= parScr, text = self.currentText, childScreen = sm.current, sharedList = self.sharedList)
            with sftp.cd('/home/public/taskapp/'):
                sftp.put(r'''C:\Users\Owen\Desktop\\Owens Generic Task App\%s.json'''%loggedUser)
        else:
            sm.current = self.childScreen
        
sm = ScreenManager()
loginscreen = LoginScreen()
loginscreen.name = 'Login Screen'
sm.add_widget(loginscreen)
screen = ShareScreen()
screen.name = 'Share Screen'
sm.add_widget(screen)
sm.current = 'Login Screen'

class TasksApp(App):
    def build(self):
        return sm


if __name__ == '__main__':
    TasksApp().run()




