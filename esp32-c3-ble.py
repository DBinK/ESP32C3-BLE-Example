import bluetooth
from micropython import const

# 定义蓝牙中断请求类型常量
_IRQ_CENTRAL_CONNECT = const(1)
_IRQ_CENTRAL_DISCONNECT = const(2)
_IRQ_GATTS_WRITE = const(3)

class BLE:
    """
    BLE 类用于初始化并管理蓝牙设备的连接和服务。
    
    参数:
        name (str): 蓝牙设备的名称
    """
    def __init__(self, name):
        self.name = name
        self.ble = bluetooth.BLE()
        self.ble.active(True)
        self.connHandle = 0
        # 标记当前未连接状态
        self.disconnected()
        # 设置蓝牙中断处理函数
        self.ble.irq(self.ble_irq)
        # 注册服务
        self.register()
        # 开始广播
        self.advertise()

    def connected(self, data):
        self.conHandle = data[0]
        print("Connected")

    def disconnected(self):
        print("Disconnected")
        pass

    """
    蓝牙中断处理函数
    """
    def ble_irq(self, event, data):
        # 中央设备尝试连接
        if event == _IRQ_CENTRAL_CONNECT:
            self.connected(data)

        # 中央设备断开连接
        elif event == _IRQ_CENTRAL_DISCONNECT:
            self.advertise()
            self.disconnected()

        # 接收到中央设备写入的数据
        elif event == _IRQ_GATTS_WRITE:
            buffer = self.ble.gatts_read(self.rx)
            message = buffer.decode("UTF-8").strip()
            self.send(message)
            print("recieve RX:", message)

    """
    注册蓝牙服务
    """
    def register(self):
        # Nordic UART Service (NUS) UUIDs
        NUS_UUID = "6E400001-B5A3-F393-E0A9-E50E24DCCA9E"
        RX_UUID = "6E400002-B5A3-F393-E0A9-E50E24DCCA9E"
        TX_UUID = "6E400003-B5A3-F393-E0A9-E50E24DCCA9E"

        BLE_NUS = bluetooth.UUID(NUS_UUID)
        BLE_RX = (bluetooth.UUID(RX_UUID), bluetooth.FLAG_WRITE)
        BLE_TX = (bluetooth.UUID(TX_UUID), bluetooth.FLAG_NOTIFY)

        BLE_UART = (
            BLE_NUS,
            (
                BLE_TX,
                BLE_RX,
            ),
        )
        SERVICES = (BLE_UART,)
        (
            (
                self.tx,
                self.rx,
            ),
        ) = self.ble.gatts_register_services(SERVICES)

    def send(self, data):
        # 向已连接的客户端发送数据
        self.ble.gatts_write(self.tx, data + "\n", True)
        print("send TX:", data)

    def advertise(self):
        # 广播蓝牙设备信息
        name = bytes(self.name, "UTF-8")
        self.ble.gap_advertise(
            100, bytearray("\x02\x01\x02") + bytearray((len(name) + 1, 0x09)) + name
        )
        print("Advertising")

if __name__ == "__main__":
    print("Starting")
    ble = BLE("ESP32 Echo") # 创建BLE实例
