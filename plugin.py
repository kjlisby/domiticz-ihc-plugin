# Python Plugin for IHCserver
#
# Author: kjlisby
#
"""
<plugin key="ihc" name="IHC via IHCServer" author="kjlisby" version="1.0.0" wikilink="http://www.domoticz.com/wiki/plugins/plugin.html" externallink="https://github.com/skumlos/ihcserver">
    <description>
        <h2>Plugin Title</h2><br/>
        IHC
        <h3>Features</h3>
        <ul style="list-style-type:square">
            <li>Creates Domoticz switches for all IHC inputs and outputs and makes Domoticz devices correspondingly.</li>
            <li>Listens to updates from IHC and updates Domoticz devices accordingly.</li>
            <li>Based on IHCServer, which must be installed, configured and running for this plugin to work.</li>
        </ul>
        <h3>Configuration</h3>
        Configuration options...
    </description>
    <params>
       <param field="Address" label="IHCServer IP Address" width="200px" required="true" default="127.0.0.1"/>
        <param field="Port" label="IHCServer Port" width="200px" required="true" default="8081"/>
        <param field="Mode6" label="Debug" width="150px">
            <options>
                <option label="None" value="0"  default="true" />
                <option label="Python Only" value="2"/>
                <option label="Basic Debugging" value="62"/>
                <option label="Basic+Messages" value="126"/>
                <option label="Connections Only" value="16"/>
                <option label="Connections+Queue" value="144"/>
                <option label="All" value="-1"/>
            </options>
        </param>
    </params>
</plugin>
"""
import Domoticz
import json
import queue
 
class BasePlugin:
    enabled = False
    def __init__(self):
        #self.var = 123
        self.heartbeatCnt = 0
        self.cmdQ = queue.Queue()
        self.ports = {}
        return

    def initPorts(self):
        if len(Devices) > 0:
            # Some devices are already defined
            for aUnit in Devices:
                Domoticz.Debug("During startup: Found port "+Devices[aUnit].DeviceID+" with Unit "+str(aUnit))
                self.ports[Devices[aUnit].DeviceID] = {
                    "DeviceID": Devices[aUnit].DeviceID, "Unit": aUnit}

    def domoticzDeviceId(self, moduleNo, port):
        if 'inputState' in port:
            return "I-"+str(moduleNo)+"-"+str(port['inputNumber'])
        else:
            return "O-"+str(moduleNo)+"-"+str(port['outputNumber'])

    def createPort(self, devID, name):
        Domoticz.Status("Creating device. Name='"+name+"' Unit="+str(self.nextDeviceId)+" DeviceID='"+devID+"'")
        if devID[0]=='O':
            image=0
        else:
            image=9
        Domoticz.Device(Name=name, Unit=self.nextDeviceId, Type=244,
                                    Subtype=73, Switchtype=0, Image=image, DeviceID=devID).Create()
        self.ports[devID] = {"DeviceID": devID, "Unit": self.nextDeviceId}
        self.nextDeviceId += 1

    def updatePortState(self, devID, state):
        Domoticz.Debug("Updating device "+devID+" "+str(state))
        targetUnit = self.ports[devID]['Unit']
        if state:
            nVal = 1
            sVal = "1"
        else:
            nVal = 0
            sVal = "0"
        Devices[targetUnit].Update(nValue=nVal, sValue=sVal)

    def updatePortName(self, devID, name):
        targetUnit = self.ports[devID]['Unit']
        if Devices[targetUnit].Name != name:
            nV = Devices[targetUnit].nValue
            sV = Devices[targetUnit].sValue
            Devices[targetUnit].Update(nValue=nV, sValue=sV, Name=name)

    def registerPort(self, moduleNo, port):
        devID = self.domoticzDeviceId(moduleNo, port)
        self.ihcIds.append(devID)
        if devID in self.ports:
            self.updatePortName(devID, port['description'])
        else:
            self.createPort(devID, port['description'])
        if 'outputState' in port:
            state = port['outputState']
        else:
            state = port['inputState']
        self.updatePortState(devID, state)

    def registerPorts(self, isInput, ihcModules):
        Domoticz.Debug("registerPorts "+str(isInput))
        for aModule in ihcModules:
            Domoticz.Debug(str(aModule))
            moduleNumber = aModule['moduleNumber']
            if 'inputStates' in aModule:
                ihcPorts = aModule['inputStates']
            elif 'outputStates' in aModule:
                ihcPorts = aModule['outputStates']
            else:
                continue
            for aPort in ihcPorts:
                self.registerPort(moduleNumber, aPort)

    def registerModules(self, ihcInputModules, ihcOutputModules):
        if (len(Devices) == 0):
            self.nextDeviceId = 1
        else:
            self.nextDeviceId = max(Devices)+1
        Domoticz.Status("REGISTERING MODULES STARTING WITH "+str(self.nextDeviceId))
        self.ihcIds = []
        self.registerPorts(True,  ihcInputModules)
        self.registerPorts(False, ihcOutputModules)
        # Remove IHC ports from Domoticz, if no longer found in IHCServer
        if len(self.ihcIds) > 0:
            # If there are no ports in IHCServer, there is something fishy going on and no ports should be deleted.
            for aPort in list(Devices.keys()):
                devID = str(Devices[aPort].DeviceID)
                if not devID in self.ihcIds:
                    Devices[aPort].Delete()

    def connectToIHCServer(self):
        Domoticz.Debug("connectToIHCServer")
        if not self.IHCServer.Connected() and not self.IHCServer.Connecting():
            Domoticz.Debug("calling self.IHCServer.Connect")
            self.IHCServer.Connect()

    def sendNextCommand(self):
        Domoticz.Debug("sendNextCommand")
        if not self.cmdQ.empty():
            self.connectToIHCServer()

    def getAllFromIHCServer(self):
        Domoticz.Debug("getAllFromIHCServer")
        postData = "{\"type\":\"getAll\"}"
#        Domoticz.Debug("postData: "+postData)
        sendMessage = { 'Verb' : 'POST',
                        'URL'  : '/ihcrequest',
                        'Data' : postData}
        Domoticz.Debug("sendMessage: "+str(sendMessage))
        self.cmdQ.put(sendMessage)
        self.sendNextCommand()

    def setInput(self, module, port, cmd):
        Domoticz.Debug("setInput "+str(module)+" "+str(port)+" "+cmd)
        if cmd=='On':
            type = "activateInput"
        else:
            type = "deactivateInput"
        postData = "{\"type\":\""+type+"\", \"moduleNumber\":"+str(module)+", \"ioNumber\":"+str(port)+"}"
#        Domoticz.Debug("postData: "+postData)
        sendMessage = { 'Verb' : 'POST',
                        'URL'  : '/ihcrequest',
                        'Data' : postData}
        Domoticz.Debug("sendMessage: "+str(sendMessage))
        self.cmdQ.put(sendMessage)
        self.sendNextCommand()

    def setOutput(self, module, port, cmd):
        Domoticz.Debug("setOutput "+str(module)+" "+str(port)+" "+cmd)
        if cmd=='On':
            state = "true"
        else:
            state = "false"
        postData = "{\"type\":\"setOutput\", \"moduleNumber\":"+str(module)+", \"ioNumber\":"+str(port)+", \"state\":"+str(state)+"}"
#        Domoticz.Debug("postData: "+postData)
        sendMessage = { 'Verb' : 'POST',
                        'URL'  : '/ihcrequest',
                        'Data' : postData}
        Domoticz.Debug("sendMessage: "+str(sendMessage))
        self.cmdQ.put(sendMessage)
        self.sendNextCommand()

    def onStart(self):
        Domoticz.Debug("onStart called")
        Domoticz.Debugging(int(Parameters["Mode6"]))
        self.initPorts()
        self.IHCServer = Domoticz.Connection(
            Name="Main", Transport="TCP/IP", Protocol="HTTP", Address=Parameters["Address"], Port=Parameters["Port"])
        self.getAllFromIHCServer()
        self.webSockConn = Domoticz.Connection(Name="Events", Transport="TCP/IP", Protocol="WS", Address=Parameters["Address"], Port=Parameters["Port"])
        self.webSockConn.Connect()

    def onStop(self):
        Domoticz.Status("onStop called")

    def onConnect(self, Connection, Status, Description):
        Domoticz.Debug("onConnect called "+Connection.Name)
        Domoticz.Debug("Connection: "+str(Connection))
        if (Status == 0):
            Domoticz.Debug("Connected successfully to: "+Parameters["Address"]+":"+Parameters["Port"])
            if Connection.Name == 'Main':
                if not self.cmdQ.empty():
                    Connection.Send(self.cmdQ.get())
            elif Connection.Name == 'Events':
                Domoticz.Debug("Server connected successfully.")
                sendData = { 'URL'  : '/ihcevents-ws',
                             'Verb': 'GET',
                             'Headers' : {  'Host': Parameters["Address"],
                                            'User-Agent': 'Domoticz/1.0',
                                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                                            'Accept-Language': 'en-GB,en;q=0.5',
                                            'Accept-Encoding': 'gzip, deflate',
                                            'Origin': 'http://'+Parameters["Address"],
                                            'Sec-WebSocket-Protocol': 'x-kaazing-handshake',
                                            'Sec-WebSocket-Extensions': 'permessage-deflate', 
                                            'Sec-WebSocket-Key': '258EAFA5-E914-47DA-95CA-C5AB0DC85B11', 
                                            'Sec-WebSocket-Version': '13', 
                                            'Connection': 'keep-alive, Upgrade',
                                            'Pragma': 'no-cache',
                                            'Cache-Control': 'no-cache',
                                            'Upgrade': 'websocket'
                                          }
                           }
                Connection.Send(sendData)
        else:
            Domoticz.Error(
                "Failed to connect to IHCServer. Status: {0} Description: {1}".format(Status, Description))
        return True

    def sendPong(self):
        postData = "{\"type\":\"pong\"}"
        sendMessage = { 'Verb' : 'POST',
                        'URL'  : '/ihcevents-ws',
                        'Data' : postData}
        Domoticz.Debug("pong: "+str(sendMessage))
        self.webSockConn.Send(sendMessage)

    def onMessage(self, Connection, Data):
        Domoticz.Debug("onMessage called "+Connection.Name)
        if Connection.Name == 'Main':
#            Domoticz.Debug("Data: "+str(Data))
            Message = json.loads(Data['Data'].decode("utf-8"))
            if not 'type' in Message:
                Domoticz.Error("Strange message: "+str(Data))
                return
            mType = Message['type']
            Domoticz.Debug("Message type = "+mType)
            if mType == "outputState":
                Domoticz.Debug(str(Message))
                module = Message['moduleNumber']
                port   = Message['outputNumber']
                state  = not Message['state']
                devID  = "O-"+str(module)+"-"+str(port)
                self.updatePortState(devID, state)
            elif mType == "inputState":
                Domoticz.Debug(str(Message))
                module = Message['moduleNumber']
                port   = Message['outputNumber']
                state  = Message['state']
                devID  = "I-"+str(module)+"-"+str(port)
                self.updatePortState(devID, state)
            else:
                mModules = Message['modules']
                mInputModules = mModules['inputModules']
                mOutputModules = mModules['outputModules']
                self.registerModules(mInputModules, mOutputModules)
        elif Connection.Name == 'Events':
            Domoticz.Debug("Data: "+str(Data))
            if "Status" in Data:
                Status = int(Data["Status"])
                if (Status == 101):
                    Domoticz.Debug("Event: Good Response received from server, WebSocket upgrade complete.")
                elif (Status == 200):
                    Domoticz.Debug("Event: Unexpected good Response received from server, Dropping connection.")
                    this.webSockConn = None
                elif (Status == 302):
                    Domoticz.Debug("Event: server returned a Page Moved Error.")
                    sendData = { 'Verb' : 'GET',
                                 'URL'  : Data["Headers"]["Location"],
                                 'Headers' : { 'Content-Type': 'text/xml; charset=utf-8', \
                                               'Connection': 'keep-alive', \
                                               'Accept': 'Content-Type: text/html; charset=UTF-8', \
                                               'Host': Parameters["Address"]+":"+Parameters["Port"], \
                                               'User-Agent':'Domoticz/1.0' },
                                }
                    Connection.Send(sendData)
                elif (Status == 400):
                    Domoticz.Error("Event: server returned a Bad Request Error.")
                    this.webSockConn = None
                elif (Status == 500):
                    Domoticz.Error("Event: server returned a Server Error.")
                    this.webSockConn = None
                else:
                    Domoticz.Error("Event: server returned a status: "+str(Data["Status"]))
                    this.webSockConn = None
            elif "Finish" in Data:
                Message = Data['Payload']
                Domoticz.Debug("Message = "+str(Message))
                if "Switching Protocols" in str(Message):
                    Domoticz.Debug("Switching Protocols")
                    return
                Message = json.loads(Data['Payload'])
                Domoticz.Debug("Message = "+str(Message))
                ihcType   = Message['type']
                if ihcType == 'ping':
                    self.sendPong()
                    return
                ihcModule = Message['moduleNumber']
                ihcPort   = Message['ioNumber']
                ihcState  = Message['state']
                Domoticz.Debug("IHC STATE CHANGE: "+ihcType+" "+str(ihcModule)+" "+str(ihcPort)+" "+str(ihcState))
                if ihcType == 'inputState':
                   devId = "I-"+str(ihcModule)+"-"+str(ihcPort)
                   self.updatePortState(devId, ihcState)
                if ihcType == 'outputState':
                   devId = "O-"+str(ihcModule)+"-"+str(ihcPort)
                   self.updatePortState(devId, ihcState)


    def onCommand(self, Unit, Command, Level, Hue):
        Domoticz.Debug("onCommand called for Unit " + str(Unit) + ": Parameter '" + str(Command) + "', Level: " + str(Level))
        DevID = Devices[Unit].DeviceID
        e = DevID.split('-')
        if DevID[0]=='I':
           self.setInput(e[1], e[2], Command)
        if DevID[0]=='O':
           self.setOutput(e[1], e[2], Command)

    def onNotification(self, Name, Subject, Text, Status, Priority, Sound, ImageFile):
        Domoticz.Debug("Notification: " + Name + "," + Subject + "," + Text + "," + Status + "," + str(Priority) + "," + Sound + "," + ImageFile)

    def onDisconnect(self, Connection):
        Domoticz.Debug("onDisconnect called "+Connection.Name)
        if Connection.Name == 'Main':
            self.sendNextCommand()
        elif Connection.Name == 'Events':
            Domoticz.Status("Reconnecting to IHCServer")
            self.webSockConn = Domoticz.Connection(Name="Events", Transport="TCP/IP", Protocol="WS", Address=Parameters["Address"], Port=Parameters["Port"])
            self.webSockConn.Connect()

    def onHeartbeat(self):
        Domoticz.Debug("onHeartbeat called "+str(self.heartbeatCnt))
        self.heartbeatCnt += 1
        if (self.heartbeatCnt > 180):
            self.getAllFromIHCServer()
            self.heartbeatCnt = 0
        self.sendNextCommand()
        if not self.webSockConn.Connected() and not self.webSockConn.Connecting():
            Domoticz.Status("Reconnecting to IHCServer")
            self.webSockConn = Domoticz.Connection(Name="Events", Transport="TCP/IP", Protocol="WS", Address=Parameters["Address"], Port=Parameters["Port"])
            self.webSockConn.Connect()

global _plugin
_plugin = BasePlugin()

def onStart():
    global _plugin
    _plugin.onStart()

def onStop():
    global _plugin
    _plugin.onStop()

def onConnect(Connection, Status, Description):
    global _plugin
    _plugin.onConnect(Connection, Status, Description)

def onMessage(Connection, Data):
    global _plugin
    _plugin.onMessage(Connection, Data)

def onCommand(Unit, Command, Level, Hue):
    global _plugin
    _plugin.onCommand(Unit, Command, Level, Hue)

def onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile):
    global _plugin
    _plugin.onNotification(Name, Subject, Text, Status, Priority, Sound, ImageFile)

def onDisconnect(Connection):
    global _plugin
    _plugin.onDisconnect(Connection)

def onHeartbeat():
    global _plugin
    _plugin.onHeartbeat()

    # Generic helper functions
def DumpConfigToLog():
    for x in Parameters:
        if Parameters[x] != "":
            Domoticz.Debug( "'" + x + "':'" + str(Parameters[x]) + "'")
    Domoticz.Debug("Device count: " + str(len(Devices)))
    for x in Devices:
        Domoticz.Debug("Device:           " + str(x) + " - " + str(Devices[x]))
        Domoticz.Debug("Device ID:       '" + str(Devices[x].ID) + "'")
        Domoticz.Debug("Device Name:     '" + Devices[x].Name + "'")
        Domoticz.Debug("Device nValue:    " + str(Devices[x].nValue))
        Domoticz.Debug("Device sValue:   '" + Devices[x].sValue + "'")
        Domoticz.Debug("Device LastLevel: " + str(Devices[x].LastLevel))
    return
