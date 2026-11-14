package com.example.ledger.app

import com.example.ledger.core.{Entry, Ledger}

object Main:
  def main(args: Array[String]): Unit =
    println(Ledger.balances(List(Entry("cash", 250), Entry("bank", 75))))
