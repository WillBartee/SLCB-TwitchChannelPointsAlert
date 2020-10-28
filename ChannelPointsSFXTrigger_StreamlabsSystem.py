# -*- coding: utf-8 -*-

#---------------------------
#   Import Libraries
#---------------------------
import clr, codecs, json, os, re, sys, threading, datetime, System

# Include the assembly with the name AnkhBotR2
clr.AddReference([asbly for asbly in System.AppDomain.CurrentDomain.GetAssemblies() if "AnkhBotR2" in str(asbly)][0])
import AnkhBotR2

clr.AddReference("IronPython.Modules.dll")
# Twitch PubSub library and dependencies
lib_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Lib")
clr.AddReferenceToFileAndPath(os.path.join(lib_path, "Microsoft.Extensions.Logging.Abstractions.dll"))
clr.AddReferenceToFileAndPath(os.path.join(lib_path, "TwitchLib.Communication.dll"))
clr.AddReferenceToFileAndPath(os.path.join(lib_path, "TwitchLib.PubSub.dll"))
# from TwitchLib.PubSub import *
# from TwitchLib.PubSub.Events import *
# sys.path.append(os.path.dirname(os.path.realpath(__file__)) + r"\References")
# clr.AddReference(r"TwitchLib.PubSub.dll")
from TwitchLib.PubSub import TwitchPubSub

#---------------------------
#   [Required] Script Information
#---------------------------
ScriptName = "Twitch Channel Points Alert Trigger"
Website = "https://www.twitch.tv/EncryptedThoughts"
Description = "Script to trigger Overlay Alert and/or SFX on channel point reward redemptions."
Creator = "WillDBot and EncryptedThoughts"
Version = "1.0.0-2.0.0.0"

#---------------------------
#   Define Global Variables
#---------------------------
SettingsFile = os.path.join(os.path.dirname(__file__), "settings.json")
SoundsDirectory = os.path.join(os.path.dirname(__file__), "Sounds")
ReadMe = os.path.join(os.path.dirname(__file__), "README.md")
EventReceiver = None
ThreadQueue = []
CurrentThread = None
PlayNextAt = datetime.datetime.now()
Sounds = {}
RewardCount = 1
WSEventName = ""

#---------------------------------------
# Classes
#---------------------------------------
class Settings(object):
    def __init__(self, SettingsFile=None):
        if SettingsFile and os.path.isfile(SettingsFile):
            with codecs.open(SettingsFile, encoding="utf-8-sig", mode="r") as f:
                self.__dict__ = json.load(f, encoding="utf-8")
        else:
            self.EnableDebug = False
            self.WSEventName = "RedeemTwitchPointAlerts"
            Reward("Test").build(None).assign(self)
            for i in range(1, RewardCount + 1):
                Reward(i).build(None).assign(self)

    def Reload(self, jsondata):
        self.__dict__ = json.loads(jsondata, encoding="utf-8", sort_keys=True, indent=2)
        return

    def Save(self, SettingsFile):
        try:
            with codecs.open(SettingsFile, encoding="utf-8-sig", mode="w+") as f:
                json.dump(self.__dict__, f, encoding="utf-8")
            with codecs.open(SettingsFile.replace("json", "js"), encoding="utf-8-sig", mode="w+") as f:
                f.write("var settings = {0};".format(json.dumps(self.__dict__, encoding='utf-8', sort_keys=True, indent=2)))
        except:
            DebugLog(ScriptName, "Failed to save settings to file.")
        return

class Reward(object):
    def __init__(self, index):
        self.index = index
        self.id = "Reward" + str(index)

    def build(self, settings):
        self.Name = getattr(settings, self.id + "Name", "")
        self.ActivationType = getattr(settings, self.id + "ActivationType", "Immediate")
        self.ImageFile = getattr(settings, self.id + "ImageFile", "")
        self.Font = getattr(settings, self.id + "Font", "Bold 70px Bangers")
        self.Duration = getattr(settings, self.id + "Duration", 5)
        self.AlignHorizontal = getattr(settings, self.id + "AlignHorizontal", 5)
        self.AlignVertical = getattr(settings, self.id + "AlignVertical", 5)
        self.Color = getattr(settings, self.id + "Color", 5)
        self.ExpandDirection = getattr(settings, self.id + "ExpandDirection", 5)
        self.TransitionType = getattr(settings, self.id + "TransitionType", "Scale")
        self.SFXFile = getattr(settings, self.id + "SFXFile", "")
        self.Volume = getattr(settings, self.id + "Volume", 100)
        return self

    def assign(self, obj):
        setattr(obj, self.id + "Name", self.Name)
        setattr(obj, self.id + "ActivationType", self.ActivationType)
        setattr(obj, self.id + "ImageFile", self.ImageFile)
        setattr(obj, self.id + "Font", self.Font)
        setattr(obj, self.id + "Duration", self.Duration)
        setattr(obj, self.id + "TransitionType", self.TransitionType)
        setattr(obj, self.id + "AlignHorizontal", self.AlignHorizontal)
        setattr(obj, self.id + "AlignVertical", self.AlignVertical)
        setattr(obj, self.id + "Color", self.Color)
        setattr(obj, self.id + "ExpandDirection", self.ExpandDirection)
        setattr(obj, self.id + "SFXFile", self.SFXFile)
        setattr(obj, self.id + "Volume", self.Volume)

#---------------------------
#   [Required] Initialize Data (Only called on load)
#---------------------------
def Init():
    global ScriptSettings
    global WSEventName
    ScriptSettings = Settings(SettingsFile)
    ScriptSettings.Save(SettingsFile)

    WSEventName = ScriptSettings.WSEventName

    BuildSoundPathDict()
    return

#---------------------------
#   [Required] Execute Data / Process messages
#---------------------------
def Execute(data):
    return

#---------------------------
#   [Required] Tick method (Gets called during every iteration even when there is no incoming data)
#---------------------------
def Tick():
    global PlayNextAt
    if PlayNextAt > datetime.datetime.now():
        return

    global CurrentThread
    if CurrentThread and CurrentThread.isAlive() == False:
        CurrentThread = None

    if CurrentThread == None and len(ThreadQueue) > 0:
        DebugLog(ScriptName, "Starting new thread. " + str(PlayNextAt))
        CurrentThread = ThreadQueue.pop(0)
        CurrentThread.start()

    return

#---------------------------
#   [Optional] Parse method (Allows you to create your own custom $parameters)
#---------------------------
def Parse(parseString, userid, username, targetid, targetname, message):
    return parseString

#---------------------------
#   [Optional] Reload Settings (Called when a user clicks the Save Settings button in the Chatbot UI)
#---------------------------
def ReloadSettings(jsonData):
    DebugLog(ScriptName, "Saving settings.")

    try:
        ScriptSettings.__dict__ = json.loads(jsonData)
        ScriptSettings.Save(SettingsFile)
        DebugLog(ScriptName, "Settings saved successfully")

    except Exception as e:
        DebugLog(ScriptName, str(e))

    return

#---------------------------
#   [Optional] Unload (Called when a user reloads their scripts or closes the bot / cleanup stuff)
#---------------------------
def Unload():
    StopEventReceiver()
    return

#---------------------------
#   [Optional] ScriptToggled (Notifies you when a user disables your script or enables it)
#---------------------------
def ScriptToggled(state):
    if state:
        if EventReceiver is None:
            RestartEventReceiver()
    else:
        StopEventReceiver()

    return

#---------------------------
#   StartEventReceiver (Start twitch pubsub event receiver)
#---------------------------
def StartEventReceiver():
    DebugLog(ScriptName, "Starting receiver")

    global EventReceiver
    EventReceiver = TwitchPubSub()
    EventReceiver.OnPubSubServiceConnected += EventReceiverConnected
    EventReceiver.OnRewardRedeemed += EventReceiverRewardRedeemed

    try:
        EventReceiver.Connect()
    except Exception as e:
        DebugLog(ScriptName, "Unable to start event receiver. Exception: " + str(e))

#---------------------------
#   StopEventReceiver (Stop twitch pubsub event receiver)
#---------------------------
def StopEventReceiver():
    global EventReceiver
    try:
        if EventReceiver is None:
            return
        EventReceiver.Disconnect()
        DebugLog(ScriptName, "Event receiver disconnected")
        EventReceiver = None

    except Exception as e:
        DebugLog(ScriptName, "Event receiver already disconnected. Exception: " + str(e))

#---------------------------
#   RestartEventReceiver (Restart event receiver cleanly)
#---------------------------
def RestartEventReceiver():
    StopEventReceiver()
    StartEventReceiver()

#---------------------------
#   EventReceiverConnected (Twitch pubsub event callback for on connected event. Needs a valid UserID and AccessToken to function properly.)
#---------------------------
def EventReceiverConnected(sender, e):
    oauth = AnkhBotR2.Managers.GlobalManager.Instance.VMLocator.StreamerLogin.Token.replace("oauth:", "")

    headers = { "Authorization": 'OAuth ' + oauth }
    data = json.loads(Parent.GetRequest("https://id.twitch.tv/oauth2/validate", headers))

    userid = json.loads(data["response"])['user_id']

    DebugLog(ScriptName, "Event receiver connected, sending topics for channel id: " + str(userid))

    EventReceiver.ListenToRewards(userid)
    EventReceiver.SendTopics(oauth)
    return

#---------------------------
#   EventReceiverRewardRedeemed (Twitch pubsub event callback for a detected redeemed channel point reward.)
#---------------------------
def EventReceiverRewardRedeemed(sender, e):
    DebugLog(ScriptName, "Event triggered: " + str(e.TimeStamp) + " ChannelId: " + str(e.ChannelId) + " Login: " + str(e.Login) + " DisplayName: " + str(e.DisplayName) + " Message: " + str(e.Message) + " RewardId: " + str(e.RewardId) + " RewardTitle: " + str(e.RewardTitle) + " RewardPrompt: " + str(e.RewardPrompt) + " RewardCost: " + str(e.RewardCost) + " Status: " + str(e.Status))

    for i in range(1, RewardCount + 1):
        rewardId = "Reward" + str(i)
        rewardName = getattr(ScriptSettings, rewardId + "Name")
        if e.RewardTitle == rewardName and not rewardName.isspace():
            rewardType = getattr(ScriptSettings, rewardId + "ActivationType")
            if (
                (rewardType == "Both")
                or (rewardType == "Immediate" and "FULFILLED" in e.Status)
                or (rewardType == r"On Reward Queue Accept/Reject" and "ACTION_TAKEN" in e.Status)
            ):
                ThreadQueue.append(threading.Thread(target=RewardRedeemedWorker,args=(e, str(i))))

    return

#---------------------------
#   RewardRedeemedWorker (Worker function to be spun off into its own thread to complete without blocking the rest of script execution.)
#---------------------------
def RewardRedeemedWorker(event, rewardIndex):
    DebugLog(ScriptName, "Redeeming reward #" + rewardIndex)

    reward = Reward(rewardIndex).build(ScriptSettings)
    DebugLog(ScriptName, json.dumps(reward.__dict__))
    ImageWorker(event, reward)
    SoundWorker(reward)

    global PlayNextAt
    PlayNextAt = datetime.datetime.now() + datetime.timedelta(0, delay)

#---------------------------
#   ImageWorker (Worker function to perform the alert functionality given the reward index..)
#---------------------------
def ImageWorker(event, reward):
    # DebugLog(ScriptName, str(event))
    DebugLog(ScriptName, reward.ImageFile + " " + str(reward.TransitionType) + " " + str(reward.Duration))
    reward.Message = event.DisplayName + " redeemed " + event.RewardTitle
    if event.Message:
        reward.Message += "\n" + event.Message

    Parent.BroadcastWsEvent(WSEventName, json.dumps(reward.__dict__))

#---------------------------
#   SoundWorker (Worker function to check for the existence of the sound files then plays them)
#---------------------------
def SoundWorker(reward):
    global Sounds
    soundFilePath = None

    try:
        DebugLog("Checking", str(reward.SFXFile) + " is in " + str(Sounds.Keys))
        soundFilePath = Sounds[reward.SFXFile]
    except:
        DebugLog("MissingSound", reward.SFXFile)

    if soundFilePath is not None:
        DebugLog(ScriptName, "PlayingSound " + reward.SFXFile + " at vol: " + str(reward.Volume))
        DebugLog(ScriptName, soundFilePath)
        Parent.PlaySound(soundFilePath, reward.Volume/100.0)

#--------------------------
# BuildSoundPathDict (Builds the list of available sounds and their full paths)
#--------------------------
def BuildSoundPathDict():
    global Sounds
    for (dirpath, dirnames, filenames) in os.walk(SoundsDirectory):
        for filename in filenames:
            Sounds[filename] = os.sep.join([dirpath, filename])
    DebugLog("FoundSounds", Sounds.Keys)

#---------------------------
#   TestWS (Attached to settings button to open the readme file in the script bin.)
#---------------------------
def TestWSEvent():
    reward = Reward("Test").build(ScriptSettings)
    reward.Message = "Testing The WebSocket"
    rewardString = json.dumps(reward.__dict__)

    DebugLog("Testing", rewardString)
    Parent.BroadcastWsEvent(WSEventName, rewardString)

#---------------------------
#   OpenReadme (Attached to settings button to open the readme file in the script bin.)
#---------------------------
def OpenReadMe():
    os.startfile(ReadMe)

#---------------------------
#   DebugLog (Attached to settings button to open the readme file in the script bin.)
#---------------------------
def DebugLog(name, msg):
    if ScriptSettings.EnableDebug:
        Parent.Log(name, str(msg))
