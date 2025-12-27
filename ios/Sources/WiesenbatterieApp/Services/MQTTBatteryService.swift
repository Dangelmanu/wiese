import Foundation
import CocoaMQTT
import Combine

final class MQTTBatteryService: ObservableObject {
    @Published var socValue: String = "-"
    @Published var connectionState: ConnectionState = .connecting

    private var mqtt: CocoaMQTT?
    private let brokerURL = URL(string: "ws://donzdorf.ddns.net:1884/mqtt")!
    private let topicSOC = "Wiesenbatterie/soc/soc_percent"

    init() {
        connect()
    }

    func connect() {
        let clientID = "mqtt_battery_client_" + UUID().uuidString.prefix(8)
        let websocket = CocoaMQTTTransport.ws(brokerURL)
        let client = CocoaMQTT(clientID: String(clientID), host: brokerURL.host ?? "donzdorf.ddns.net", port: UInt16(brokerURL.port ?? 1884))
        client.username = "mqtt"
        client.password = "Frischauf1!"
        client.autoReconnect = true
        client.autoReconnectTimeInterval = 5
        client.enableSSL = false
        client.keepAlive = 60
        client.logLevel = .debug
        client.delegate = self
        client.transport = websocket

        connectionState = .connecting
        mqtt = client
        client.connect()
    }

    private func updateSOC(from payload: String) {
        if let value = Double(payload) {
            DispatchQueue.main.async { [weak self] in
                self?.socValue = String(value)
            }
        } else {
            DispatchQueue.main.async { [weak self] in
                self?.socValue = "-"
            }
        }
    }
}

extension MQTTBatteryService: CocoaMQTTDelegate {
    func mqtt(_ mqtt: CocoaMQTT, didSubscribeTopic topics: [String]) {}
    func mqtt(_ mqtt: CocoaMQTT, didUnsubscribeTopic topic: String) {}
    func mqttDidPing(_ mqtt: CocoaMQTT) {}
    func mqttDidReceivePong(_ mqtt: CocoaMQTT) {}
    func mqttDidDisconnect(_ mqtt: CocoaMQTT, withError err: (any Error)?) {
        DispatchQueue.main.async { [weak self] in
            self?.connectionState = .disconnected
        }
    }

    func mqtt(_ mqtt: CocoaMQTT, didConnectAck ack: CocoaMQTTConnAck) {
        guard ack == .accept else {
            DispatchQueue.main.async { [weak self] in
                self?.connectionState = .error
            }
            return
        }

        DispatchQueue.main.async { [weak self] in
            self?.connectionState = .connected
        }
        mqtt.subscribe(topicSOC)
    }

    func mqtt(_ mqtt: CocoaMQTT, didReceiveMessage message: CocoaMQTTMessage, id: UInt16) {
        updateSOC(from: message.string ?? "")
    }

    func mqtt(_ mqtt: CocoaMQTT, didPublishMessage message: CocoaMQTTMessage, id: UInt16) {}
    func mqtt(_ mqtt: CocoaMQTT, didPublishAck id: UInt16) {}

    func mqtt(_ mqtt: CocoaMQTT, didStateChangeTo state: CocoaMQTTConnState) {
        DispatchQueue.main.async { [weak self] in
            switch state {
            case .connecting, .initial:
                self?.connectionState = .connecting
            case .connected:
                self?.connectionState = .connected
            case .disconnected:
                self?.connectionState = .disconnected
            case .error:
                self?.connectionState = .error
            case .closing:
                self?.connectionState = .offline
            }
        }
    }

    func mqtt(_ mqtt: CocoaMQTT, didReceive trust: SecTrust, completionHandler: @escaping (Bool) -> Void) {
        completionHandler(true)
    }

    func mqtt(_ mqtt: CocoaMQTT, didPublishComplete id: UInt16) {}
    func mqtt(_ mqtt: CocoaMQTT, didReceive connAck: CocoaMQTTConnAck) {}
    func mqtt(_ mqtt: CocoaMQTT, didReconnect reason: CocoaMQTTReconnectReason) {}
}
