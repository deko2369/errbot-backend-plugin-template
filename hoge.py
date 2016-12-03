# -*- coding: utf-8 -*-
from errbot.backends.base import Message, ONLINE, Room, \
                                    RoomOccupant, Identifier
from errbot.core import ErrBot

# Can't use __name__ because of Yapsy
log = logging.getLogger('errbot.backends.hoge')

# Hogeチャットシステムのライブラリを読み込む(ライブラリは実在しません)
try:
    import HogeChatClient
except ImportError:
    log.exception("Could not start the hoge backend")
    log.fatal(
        "You need to install the HogeChatClient package in order "
        "to use the Hoge backend. "
        "You should be able to install this package using: "
        "pip install HogeChatClient"
    )
    sys.exit(1)

class HogeUser(Identifier):
    """
    チャットシステムのユーザーを表現するクラス

    直接このクラスをインスタンス化せず、Backendクラスのbuild_identifierメソッドの中で
    オブジェクトを生成するようにする

    ref. http://errbot.io/en/latest/errbot.backends.base.html#errbot.backends.base.Identifier
    """
    def __init__(self, username, bot):
        """
        ユーザーを初期化する

        usernameはチャットシステムで利用されている名前を指定
        """
        self._username = username
        self._bot = bot

    @property
    def username(self):
        """
        ユーザーの名前を返す
        """
        self return._username

class HogeRoomOccupant(RoomOccupant, HogeUser):
    """
    チャットシステムのチャットルームにいるユーザーを表現するクラス

    ref. http://errbot.io/en/latest/errbot.backends.base.html#errbot.backends.base.RoomOccupant
    """
    def __init__(self, username, roomname, bot):
        """
        特定のチャットルームにいるユーザーを初期化する
        """
        super().__init__(username, bot)
        self._room = HogeRoom(roomname, bot)

    @property
    def room(self):
        """
        ルーム情報を返す
        """
        return self._room

class HogeBackend(ErrBot):
    """
    Backendクラス本体

    ここにチャットシステムの実際のやりとりを書いていく
    """
    def __init__(self, config):
        """
        初期設定
        """
        super().__init__(config)
        identity = config.BOT_IDENTIY
        self.token = identity.get('token', None)
        if not self.token:
            log.fatal(
                'You need to set your token in the BOT_IDENTITY setting '
                'in your config.py .'
            )
            sys.exit(1)

        # tokenを指定してクライアントを初期化
        self.client = HogeChatClient.Client(self.token)

        # bot自身のidentifierを作成
        self.bot_identifier = HogeUser('BOT NAME', self)

    def build_reply(self, mess, text=None, private=False):
        """
        返信メッセージを作成する
        """
        # メッセージを構築
        response = self.build_message(text)
        # 返信元のIdentifier
        response.frm = self.bot_identifier
        # 返信先のIdentifier
        response.to = mess.frm

        return response

    def prefix_groupchat_reply(self, message, identifier):
        """
        グループチャットへの返信メッセージのテンプレ
        """
        message.body = '@%s %s' % (identifier.username, message.text)

    def build_message(self, text):
        """
        メッセージオブジェクトの作成
        """
        return super().build_message(text)

    def build_identifier(self, text_repf):
        """
        Identifierオブジェクトの作成

        Hogeチャットシステムは以下の書式でIdentifierを構築する
        ユーザー: @<username>
        チャットルームにいるユーザー: @<username>#<roomname>
        """
        text = text_repr.strip()

        if text.startswith('@') and '#' not in text:
            return HogeUser(text.split('@')[1], self)
        elif '#' in text:
            username, roomname = text.split('#')
            return HogeRoomOccupant(username.split('@')[1], roomname, self)
        
        raise RuntimeError('Unrecognized identifier: %s' % text)

    def serve_once(self):
        """
        チャットシステムから新着メッセージを受け取り処理を行うメソッド

        このserve_onceメソッドはErrBotから定期的にコールされる
        似たようなオーバーライド対象メソッドにserve_foreverもある

        ref. http://errbot.io/en/latest/errbot.backends.base.html#errbot.backends.base.Backend.serve_forever
        """
        # 新着メッセージを取得
        mess = self.client.new_messages()

        # 取得したメッセージを順番に処理
        # メッセージにはユーザー名と発言されたルーム名も格納されている
        for msg in mess:
            # Messageオブジェクトを構築
            m = Message(msg)
            m.frm = HogeRoomOccupant(msg.username, msg.roomname, self)
            m.to = HogeRoom(msg.roomname, self)

            # メッセージのコールバックを呼び出す
            self.callback_message(m)

            # @<username>が含まれている場合はcallback_mentionも呼び出す
            # 詳細な実装を省いているので注意
            if '@' in msg:
                mentions = [HogeUser(username, self), ...]
                self.callback_mention(m, mentions)

    def send_message(self, mess):
        """
        チャットシステムへの送信部分の実装
        """
        self.client.send(mess.body)

    def connect(self):
        """
        チャットシステムのライブラリのコネクションを返却
        """
        return self.client

    def query_room(self, room)
        """
        roomの文字列からHogeRoomのオブジェクトを返却する処理
        """
        r = self.client.room_info(room)
        return HogeRoom(r.name, self)

    @property
    def mode(self):
        """
        現在のバックエンドを示すユニークな文字列
        """
        return 'hoge'

    @property
    def rooms(self):
        """
        botの入室しているRoomインスタンスを返却
        """
        return []

    def change_presense(self, status=ONLINE, message=''):
        """
        botの入室ステータスが変化するときに呼び出される処理
        """
        super().change_presence(status=status, message=message)

class HogeRoom(Room):
    """
    Hogeチャットシステムのチャットルームについての定義

    チャットルームに対してbotが参加したり、作成したりする機能を実装する
    チャットシステムのクライアントがそういった機能を提供していない場合は実装不可能...

    ref. http://errbot.io/en/latest/errbot.backends.base.html#errbot.backends.base.Room
    """
    def __init__(self, name, bot):
        self._name = name
        self._bot = bot

    def join(self, username=None, password=None):
        """
        botが部屋にjoinする
        """
        self._bot.client.join_room(self._name)

    def leave(self, reason=None):
        """
        botが部屋からleaveする
        """
        self._bot.client.leave_room(self._name)

    def create(self):
        """
        botが部屋をcreateする
        """
        self._bot.client.create_room(self._name)

    def destroy(self):
        """
        botが部屋をdestroyする
        """
        self._bot.client.destroy_room(self._name)

    @property
    def exists(self):
        """
        部屋が存在するかどうか
        """
        return self._bot.client.exist_room(self._name)

    @property
    def joined(self):
        """
        botが部屋にjoinしているかどうか
        """
        return self._bot.client.is_joined(self._name)

    @property
    def topic(self):
        """
        部屋のトピックを取得
        """
        return self._bot.client.room_info(self._name).topic

    @topic.setter
    def topic(self, topic):
        """
        部屋のトピックを設定
        """
        return self._bot.client.set_room_topic(self._name, topic)

    @property
    def occupants(self):
        """
        部屋に存在するユーザーのIdentifierを取得
        """
        return [HogeUser(name, self._bot) \
                for name in self._bot.client.get_room_usernames(self._name)]

    def invite(self, *args):
        """
        部屋にユーザーを招待
        """
        for ident in args:
            self._bot.client.invite(self._name, ident.username)

