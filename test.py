import ch

class Test(ch.RoomConnection):
        def onConnect(self):
                print("Connected")
                self.enableBg()
                self.enableRecording()
                self.setNameColor("000")
                self.setFontColor("000")
                self.setFontFace("2")
                self.setFontSize(10)
                self.message("Master called?")
        
        def onHistoryMessage(self, user, message):
                print(user.name, message.body)
        
        def onMessage(self, user, message):
                print(user.name, message.body)
                if self.user == user: return
                elif message.body == "<3":
                        self.message("fag :3")
                if message.body == "mods":
                        self.message(", ".join(self.modnames))
                if message.body == "Hey Slave!":
                        if user == ch.User("quadrant"):
                                self.message("Yes master?")

                if message.body == "Restart":
                        self.reconnect()
                        self.message("I'm back!")
                        print ("Successfully Reconnected to Chat")

        def onFloodWarning(self):
                self.reconnect()
        
        def onJoin(self, user):
                self.message("hai, " + user.name + "! x3")
        
        def onLeave(self, user):
                self.message("bai, " + user.name + "! T.T")

Test.easy_start(room = "naruto-tv", name = "QuadrantsBitch", password="popeyjack")
