import json
from channels.generic.websocket import AsyncWebsocketConsumer
from utils import ssh
from assets.models import Machine


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.history = []
        self.now_cd = ""
        self.cmd = ""
        self.last_cd = ""
        self.up_num = 0
        self.result = ""
        self.room_name = self.scope['url_route']['kwargs']['id']
        self.room_group_name = 'chat_%s' % self.room_name
        self.machine = Machine.objects.filter(id=self.room_name).first()
        self.host = ssh.SSH2(hostname=self.machine.ip_address,
                             port=self.machine.port,
                             username=self.machine.username,
                             password=self.machine.password)

        # Join room group
        await self.channel_layer.group_add(self.room_group_name,
                                           self.channel_name)

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(self.room_group_name,
                                               self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        msg = await self.host_chat(text_data)
        # self.result = "\r$ "
        text_data_json = {"message": msg}
        # text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # Send message to room group
        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'chat_message',
            'message': message
        })

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        await self.send(text_data=message)
        # await self.send(text_data=json.dumps(message))
        # await self.send(text_data=json.dumps({'message': message}))

    async def host_chat(self, message):
        self.result = ""
        if "\r" not in message:
            if message == '\177':
                print("删除键被按了")
                self.cmd = cmd[:len(cmd) - 1]
            elif message == '\003':  # ctrl + c
                self.cmd = ""
            elif message == '\x1b[A':  # 上
                print("按了上键")
                self.up_num += 1
                if self.up_num == 10:
                    self.up_num = 0
                    self.cmd = ""
                else:
                    self.cmd = self.history[len(self.history) - self.up_num]
            elif message == '\x1b[B':  # 下
                print("按了下键")
                self.up_num -= 1
                if self.up_num > 0:
                    self.cmd = self.history[len(self.history) - self.up_num]
            elif message == '\x1b[D':  # 左
                print("按了左键")
            elif message == '\x1b[C':  # 右
                print("按了右键")
            else:
                self.up_num = 0
                self.cmd += message
        else:
            try:
                self.cmd = self.cmd.strip()
                if self.cmd != "":
                    self.history.append(self.cmd)
                    if len(self.history) > 10:
                        self.history = self.history[1:]
                    if "cd " in self.cmd:
                        self.last_cd = self.now_cd
                        self.now_cd = self.cmd
                    if self.now_cd != "":
                        self.cmd = self.now_cd + ";" + self.cmd
                    out, err = self.host.do(self.cmd)
                    self.cmd = ""
                    if err:
                        if "cd: " in err:
                            self.now_cd = self.last_cd
                        self.result = "\x1B[1;3;31m " + err + " \x1B[0m\r$ "
                    else:
                        self.result = out + "\r$ "
            except Exception as err:
                self.result = "\x1B[1;3;31m " + str(err) + " \x1B[0m\r$ "
        return self.result