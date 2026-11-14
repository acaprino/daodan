import XCTest
@testable import ShopKit

final class PriceTests: XCTestCase {
    func testFormatted() {
        XCTAssertEqual(Price(cents: 1250).formatted, "12.50")
    }
}
