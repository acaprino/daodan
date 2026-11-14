import Foundation

public struct Price: Equatable {
    public let cents: Int

    public init(cents: Int) {
        self.cents = cents
    }

    public var formatted: String {
        String(format: "%d.%02d", cents / 100, cents % 100)
    }
}
