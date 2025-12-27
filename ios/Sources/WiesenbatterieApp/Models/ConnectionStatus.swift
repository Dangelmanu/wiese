import Foundation
import SwiftUI

enum ConnectionState {
    case connecting
    case connected
    case error
    case offline
    case disconnected

    var statusText: String {
        switch self {
        case .connecting:
            return "Verbinde..."
        case .connected:
            return "Verbunden"
        case .error:
            return "Verbindungsfehler"
        case .offline:
            return "Offline"
        case .disconnected:
            return "Getrennt"
        }
    }

    var statusColor: Color {
        switch self {
        case .connected:
            return Color.green
        case .connecting:
            return Color.secondary
        case .error, .offline, .disconnected:
            return Color.red
        }
    }
}
