import threading

from server import Server


class Thread_Server(Server):

    def Create_New_Thread(self,Session_Id):

        Session_Thread=threading.Thread()

        self.Thread_Mapping[Session_Id]=Session_Thread


    def Handle_Client(self):




    def Hand_Over_To_Threads(self,Session_Id):

        self.Thread_Mapping[Session_Id].Thread(target=self.Handle_Client)







        



