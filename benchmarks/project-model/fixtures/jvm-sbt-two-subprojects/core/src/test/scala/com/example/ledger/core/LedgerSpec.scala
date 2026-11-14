package com.example.ledger.core

import org.scalatest.funsuite.AnyFunSuite

class LedgerSpec extends AnyFunSuite:
  test("sums entries per account") {
    val entries = List(Entry("cash", 100), Entry("cash", -40), Entry("bank", 10))
    assert(Ledger.balances(entries) == Map("cash" -> 60L, "bank" -> 10L))
  }
